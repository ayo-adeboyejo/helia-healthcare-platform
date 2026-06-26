import uuid
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Appointment(Base):
    __tablename__ = "appointments"

    id:             Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id:     Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    doctor_id:      Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    appointment_date: Mapped[date]        = mapped_column(Date, nullable=False)
    start_time:     Mapped[str]           = mapped_column(String(5), nullable=False)   # HH:MM
    end_time:       Mapped[str]           = mapped_column(String(5), nullable=False)   # HH:MM
    status:         Mapped[str]           = mapped_column(String(20), nullable=False, default="scheduled")
    # scheduled | confirmed | completed | cancelled | no_show
    reason:         Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes:          Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consultation_fee: Mapped[float]       = mapped_column(Float, default=0.0)
    is_recurring:   Mapped[bool]          = mapped_column(Boolean, default=False)
    recurring_rule_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Waitlist(Base):
    __tablename__ = "waitlist"

    id:          Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id:  Mapped[str]      = mapped_column(String(36), nullable=False, index=True)
    doctor_id:   Mapped[str]      = mapped_column(String(36), nullable=False, index=True)
    preferred_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    preferred_time: Mapped[Optional[str]]  = mapped_column(String(5), nullable=True)
    status:      Mapped[str]      = mapped_column(String(20), default="waiting")  # waiting | notified | booked | expired
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RecurringRule(Base):
    __tablename__ = "recurring_rules"

    id:            Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id:    Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    doctor_id:     Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    frequency:     Mapped[str]           = mapped_column(String(20), nullable=False)  # weekly | biweekly | monthly
    start_date:    Mapped[date]          = mapped_column(Date, nullable=False)
    end_date:      Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time:    Mapped[str]           = mapped_column(String(5), nullable=False)
    is_active:     Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
