import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logger import logger
from app.models.payment import Payment, Invoice, DoctorEarning
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse,
    InvoiceResponse, DoctorEarningResponse, RefundRequest,
)

router = APIRouter()

PLATFORM_FEE_PERCENT = 0.10  # 10% platform commission


def utcnow():
    return datetime.now(timezone.utc)


def generate_invoice_number() -> str:
    import random
    return f"INV-{datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"


# ── Create payment record ─────────────────────────────────────────────────────
@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    payment = Payment(
        appointment_id=payload.appointment_id,
        patient_id=current_user["user_id"],
        doctor_id=payload.doctor_id,
        amount=payload.amount,
        currency=payload.currency,
        payment_method=payload.payment_method,
        status="pending",
    )
    db.add(payment)
    await db.flush()

    # Create invoice
    tax = round(payload.amount * 0.0, 2)  # No VAT on medical consultations in UK
    invoice = Invoice(
        payment_id=payment.id,
        patient_id=current_user["user_id"],
        invoice_number=generate_invoice_number(),
        amount=payload.amount,
        tax=tax,
        total=payload.amount + tax,
        status="issued",
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(payment)

    logger.info(f"payment_created id={payment.id} amount={payload.amount} patient={current_user['user_id']}")
    return payment


# ── Confirm payment ───────────────────────────────────────────────────────────
@router.put("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.patient_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    payment.status = "paid"
    payment.paid_at = utcnow()
    await db.flush()

    # Record doctor earning
    platform_fee = round(payment.amount * PLATFORM_FEE_PERCENT, 2)
    earning = DoctorEarning(
        doctor_id=payment.doctor_id,
        payment_id=payment.id,
        amount=payment.amount,
        platform_fee=platform_fee,
        net_amount=round(payment.amount - platform_fee, 2),
        status="pending",
    )
    db.add(earning)
    await db.commit()
    await db.refresh(payment)

    logger.info(f"payment_confirmed id={payment_id} amount={payment.amount}")
    return payment


# ── Get patient payments ──────────────────────────────────────────────────────
@router.get("/payments", response_model=List[PaymentResponse])
async def get_my_payments(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Payment).where(Payment.patient_id == current_user["user_id"])
    if status:
        query = query.where(Payment.status == status)
    query = query.order_by(Payment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


# ── Get invoices ──────────────────────────────────────────────────────────────
@router.get("/payments/invoices", response_model=List[InvoiceResponse])
async def get_my_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .where(Invoice.patient_id == current_user["user_id"])
        .order_by(Invoice.issued_at.desc())
    )
    return result.scalars().all()


# ── Doctor earnings ───────────────────────────────────────────────────────────
@router.get("/payments/earnings", response_model=List[DoctorEarningResponse])
async def get_doctor_earnings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Doctor access required")
    result = await db.execute(
        select(DoctorEarning)
        .where(DoctorEarning.doctor_id == current_user["user_id"])
        .order_by(DoctorEarning.created_at.desc())
    )
    return result.scalars().all()


# ── Refund ────────────────────────────────────────────────────────────────────
@router.post("/payments/refund", response_model=PaymentResponse)
async def refund_payment(
    payload: RefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Payment).where(Payment.id == payload.payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "paid":
        raise HTTPException(status_code=400, detail="Only paid payments can be refunded")

    payment.status = "refunded"
    payment.notes = payload.reason
    await db.commit()
    await db.refresh(payment)

    logger.info(f"payment_refunded id={payload.payment_id}")
    return payment
