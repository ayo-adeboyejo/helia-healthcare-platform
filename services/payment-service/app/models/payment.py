import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Payment(Base):
    __tablename__ = "payments"

    id:             Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id: Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    patient_id:     Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    doctor_id:      Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    amount:         Mapped[float]         = mapped_column(Float, nullable=False)
    currency:       Mapped[str]           = mapped_column(String(3), default="GBP")
    status:         Mapped[str]           = mapped_column(String(20), default="pending")
    # pending | paid | refunded | failed
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes:          Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paid_at:        Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Invoice(Base):
    __tablename__ = "invoices"

    id:             Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id:     Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    patient_id:     Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    invoice_number: Mapped[str]           = mapped_column(String(20), unique=True, nullable=False)
    amount:         Mapped[float]         = mapped_column(Float, nullable=False)
    tax:            Mapped[float]         = mapped_column(Float, default=0.0)
    total:          Mapped[float]         = mapped_column(Float, nullable=False)
    status:         Mapped[str]           = mapped_column(String(20), default="issued")
    issued_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)


class DoctorEarning(Base):
    __tablename__ = "doctor_earnings"

    id:             Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id:      Mapped[str]      = mapped_column(String(36), nullable=False, index=True)
    payment_id:     Mapped[str]      = mapped_column(String(36), nullable=False)
    amount:         Mapped[float]    = mapped_column(Float, nullable=False)
    platform_fee:   Mapped[float]    = mapped_column(Float, default=0.0)
    net_amount:     Mapped[float]    = mapped_column(Float, nullable=False)
    status:         Mapped[str]      = mapped_column(String(20), default="pending")
    created_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
