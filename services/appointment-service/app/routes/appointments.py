from datetime import datetime, timedelta, timezone, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from redis.asyncio import Redis
import httpx

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.dependencies import get_current_user
from app.core.logger import logger
from app.models.appointment import Appointment, Waitlist, RecurringRule
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    WaitlistCreate, WaitlistResponse, SlotResponse,
)
from app.config import settings

router = APIRouter()


def utcnow():
    return datetime.now(timezone.utc)


def calculate_end_time(start_time: str, duration_minutes: int = 30) -> str:
    h, m = map(int, start_time.split(":"))
    total = h * 60 + m + duration_minutes
    return f"{total // 60:02d}:{total % 60:02d}"


# ── Check available slots for a doctor on a date ──────────────────────────────
@router.get("/appointments/slots", response_model=List[SlotResponse])
async def get_available_slots(
    doctor_id: str = Query(...),
    date:      str = Query(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    cache_key = f"slots:{doctor_id}:{date}"
    cached = await redis.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    # Get booked slots for this doctor on this date
    result = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == date,
                Appointment.status.in_(["scheduled", "confirmed"]),
            )
        )
    )
    booked = {a.start_time for a in result.scalars().all()}

    # Fetch doctor availability from user-service
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.user_service_url}/doctors/{doctor_id}/availability",
                timeout=10.0,
            )
        availability = resp.json() if resp.status_code == 200 else []
    except Exception:
        availability = []

    # Build slot list from availability
    slots = []
    appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
    day_of_week = appointment_date.weekday()  # 0=Monday

    for avail in availability:
        if avail.get("day_of_week") != day_of_week:
            continue
        duration = avail.get("slot_duration", 30)
        start_h, start_m = map(int, avail["start_time"].split(":"))
        end_h, end_m = map(int, avail["end_time"].split(":"))
        current = start_h * 60 + start_m
        end = end_h * 60 + end_m

        while current + duration <= end:
            time_str = f"{current // 60:02d}:{current % 60:02d}"
            slots.append({
                "time":      time_str,
                "available": time_str not in booked,
            })
            current += duration

    # Cache for 5 minutes
    import json
    await redis.setex(cache_key, 300, json.dumps(slots))
    return slots


# ── Book appointment ──────────────────────────────────────────────────────────
@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def book_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    patient_id = current_user["user_id"]

    # Atomic slot lock — prevents double booking
    lock_key = f"slot_lock:{payload.doctor_id}:{payload.appointment_date}:{payload.start_time}"
    locked = await redis.set(lock_key, patient_id, nx=True, ex=30)
    if not locked:
        raise HTTPException(status_code=409, detail="This slot is currently being booked. Please try again.")

    try:
        # Check if slot is already booked in DB
        existing = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.doctor_id == payload.doctor_id,
                    Appointment.appointment_date == payload.appointment_date,
                    Appointment.start_time == payload.start_time,
                    Appointment.status.in_(["scheduled", "confirmed"]),
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="This slot is already booked")

        # Fetch doctor info for fee
        consultation_fee = 0.0
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.user_service_url}/doctors/{payload.doctor_id}",
                    timeout=10.0,
                )
            if resp.status_code == 200:
                consultation_fee = resp.json().get("consultation_fee", 0.0)
        except Exception:
            pass

        end_time = calculate_end_time(payload.start_time)

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=payload.doctor_id,
            appointment_date=payload.appointment_date,
            start_time=payload.start_time,
            end_time=end_time,
            reason=payload.reason,
            consultation_fee=consultation_fee,
            is_recurring=payload.is_recurring,
            status="scheduled",
        )
        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)

        # Invalidate slot cache
        await redis.delete(f"slots:{payload.doctor_id}:{payload.appointment_date}")

        # Notify waitlist
        await notify_waitlist(payload.doctor_id, str(payload.appointment_date), db, redis)

        logger.info(f"appointment_booked id={appointment.id} patient={patient_id} doctor={payload.doctor_id}")
        return appointment

    finally:
        await redis.delete(lock_key)


# ── Get patient appointments ───────────────────────────────────────────────────
@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_my_appointments(
    status:   Optional[str] = Query(None),
    limit:    int = Query(20, le=100),
    offset:   int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Appointment).where(Appointment.patient_id == current_user["user_id"])
    if status:
        query = query.where(Appointment.status == status)
    query = query.order_by(Appointment.appointment_date.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


# ── Get doctor appointments ────────────────────────────────────────────────────
@router.get("/appointments/doctor/{doctor_id}", response_model=List[AppointmentResponse])
async def get_doctor_appointments(
    doctor_id: str,
    date:      Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Appointment).where(Appointment.doctor_id == doctor_id)
    if date:
        query = query.where(Appointment.appointment_date == date)
    query = query.order_by(Appointment.appointment_date, Appointment.start_time)
    result = await db.execute(query)
    return result.scalars().all()


# ── Get single appointment ────────────────────────────────────────────────────
@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.patient_id != current_user["user_id"] and appointment.doctor_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return appointment


# ── Update appointment ────────────────────────────────────────────────────────
@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = payload.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(appointment, key, val)

    await db.commit()
    await db.refresh(appointment)

    # Invalidate slot cache
    await redis.delete(f"slots:{appointment.doctor_id}:{appointment.appointment_date}")
    return appointment


# ── Cancel appointment ────────────────────────────────────────────────────────
@router.delete("/appointments/{appointment_id}", response_model=dict)
async def cancel_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.patient_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    appointment.status = "cancelled"
    await db.commit()

    # Free the slot and notify waitlist
    await redis.delete(f"slots:{appointment.doctor_id}:{appointment.appointment_date}")
    await notify_waitlist(appointment.doctor_id, str(appointment.appointment_date), db, redis)

    logger.info(f"appointment_cancelled id={appointment_id}")
    return {"message": "Appointment cancelled successfully"}


# ── Waitlist ──────────────────────────────────────────────────────────────────
@router.post("/appointments/waitlist", response_model=WaitlistResponse, status_code=201)
async def join_waitlist(
    payload: WaitlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    entry = Waitlist(
        patient_id=current_user["user_id"],
        doctor_id=payload.doctor_id,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        status="waiting",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    logger.info(f"waitlist_joined patient={current_user['user_id']} doctor={payload.doctor_id}")
    return entry


async def notify_waitlist(doctor_id: str, date: str, db: AsyncSession, redis: Redis):
    """Notify first waiting patient when a slot becomes available."""
    result = await db.execute(
        select(Waitlist).where(
            and_(
                Waitlist.doctor_id == doctor_id,
                Waitlist.status == "waiting",
            )
        ).order_by(Waitlist.created_at).limit(1)
    )
    entry = result.scalar_one_or_none()
    if entry:
        entry.status = "notified"
        await db.commit()
        logger.info(f"waitlist_notified patient={entry.patient_id} doctor={doctor_id}")
