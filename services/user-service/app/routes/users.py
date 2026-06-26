from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Patient, Doctor, Specialty, AvailabilitySlot, DoctorReview
from app.schemas.user import (
    PatientCreate, PatientUpdate, PatientResponse,
    DoctorCreate, DoctorUpdate, DoctorResponse,
    SpecialtyCreate, SpecialtyResponse,
    AvailabilitySlotCreate, AvailabilitySlotResponse,
    ReviewCreate, ReviewResponse,
)

router = APIRouter()


# ── Patients ──────────────────────────────────────────────────────────────────

@router.post("/patients", response_model=PatientResponse, status_code=201)
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    existing = await db.execute(select(Patient).where(Patient.user_id == payload.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Patient profile already exists")

    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/patients/{user_id}", response_model=PatientResponse)
async def get_patient(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.user_id == user_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/patients/{user_id}", response_model=PatientResponse)
async def update_patient(
    user_id: str,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.user_id == user_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = payload.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(patient, key, val)

    await db.commit()
    await db.refresh(patient)
    return patient


# ── Specialties ───────────────────────────────────────────────────────────────

@router.get("/specialties", response_model=List[SpecialtyResponse])
async def list_specialties(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Specialty).order_by(Specialty.name))
    return result.scalars().all()


@router.post("/specialties", response_model=SpecialtyResponse, status_code=201)
async def create_specialty(
    payload: SpecialtyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    specialty = Specialty(**payload.model_dump())
    db.add(specialty)
    await db.commit()
    await db.refresh(specialty)
    return specialty


# ── Doctors ───────────────────────────────────────────────────────────────────

@router.post("/doctors", response_model=DoctorResponse, status_code=201)
async def create_doctor(
    payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    existing = await db.execute(select(Doctor).where(Doctor.user_id == payload.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Doctor profile already exists")

    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.get("/doctors", response_model=List[DoctorResponse])
async def list_doctors(
    specialty_id: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    min_fee:      Optional[float] = Query(None),
    max_fee:      Optional[float] = Query(None),
    min_rating:   Optional[float] = Query(None),
    limit:        int = Query(20, le=100),
    offset:       int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Doctor).where(Doctor.is_approved == True)
    if specialty_id:  query = query.where(Doctor.specialty_id == specialty_id)
    if is_available is not None: query = query.where(Doctor.is_available == is_available)
    if min_fee:       query = query.where(Doctor.consultation_fee >= min_fee)
    if max_fee:       query = query.where(Doctor.consultation_fee <= max_fee)
    if min_rating:    query = query.where(Doctor.rating >= min_rating)
    query = query.order_by(Doctor.rating.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.put("/doctors/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: str,
    payload: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    update_data = payload.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(doctor, key, val)

    await db.commit()
    await db.refresh(doctor)
    return doctor


# ── Availability slots ────────────────────────────────────────────────────────

@router.post("/doctors/{doctor_id}/availability", response_model=AvailabilitySlotResponse, status_code=201)
async def add_availability(
    doctor_id: str,
    payload: AvailabilitySlotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    slot = AvailabilitySlot(**payload.model_dump(), doctor_id=doctor_id)
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return slot


@router.get("/doctors/{doctor_id}/availability", response_model=List[AvailabilitySlotResponse])
async def get_availability(doctor_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AvailabilitySlot)
        .where(AvailabilitySlot.doctor_id == doctor_id, AvailabilitySlot.is_active == True)
        .order_by(AvailabilitySlot.day_of_week, AvailabilitySlot.start_time)
    )
    return result.scalars().all()


# ── Reviews ───────────────────────────────────────────────────────────────────

@router.post("/doctors/{doctor_id}/reviews", response_model=ReviewResponse, status_code=201)
async def add_review(
    doctor_id: str,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    review = DoctorReview(**payload.model_dump(), doctor_id=doctor_id)
    db.add(review)
    await db.flush()

    # Update doctor average rating
    avg_result = await db.execute(
        select(func.avg(DoctorReview.rating), func.count(DoctorReview.id))
        .where(DoctorReview.doctor_id == doctor_id)
    )
    avg_rating, count = avg_result.first()
    await db.execute(
        update(Doctor)
        .where(Doctor.id == doctor_id)
        .values(rating=round(float(avg_rating), 1), total_reviews=count)
    )
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/doctors/{doctor_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    doctor_id: str,
    limit: int = Query(10, le=50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DoctorReview)
        .where(DoctorReview.doctor_id == doctor_id)
        .order_by(DoctorReview.created_at.desc())
        .limit(limit).offset(offset)
    )
    return result.scalars().all()
