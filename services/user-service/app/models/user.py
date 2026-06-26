import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id:           Mapped[str]            = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:      Mapped[str]            = mapped_column(String(36), unique=True, nullable=False, index=True)
    first_name:   Mapped[str]            = mapped_column(String(100), nullable=False)
    last_name:    Mapped[str]            = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gender:       Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)
    phone:        Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)
    address:      Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    blood_type:   Mapped[Optional[str]]  = mapped_column(String(5), nullable=True)
    allergies:    Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    avatar_url:   Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    created_at:   Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:   Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Specialty(Base):
    __tablename__ = "specialties"

    id:          Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name:        Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon:        Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class Doctor(Base):
    __tablename__ = "doctors"

    id:                Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:           Mapped[str]           = mapped_column(String(36), unique=True, nullable=False, index=True)
    first_name:        Mapped[str]           = mapped_column(String(100), nullable=False)
    last_name:         Mapped[str]           = mapped_column(String(100), nullable=False)
    specialty_id:      Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    qualification:     Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_years:  Mapped[int]           = mapped_column(Integer, default=0)
    bio:               Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consultation_fee:  Mapped[float]         = mapped_column(Float, default=0.0)
    languages:         Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # comma-separated
    phone:             Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    clinic_address:    Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url:        Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_approved:       Mapped[bool]          = mapped_column(Boolean, default=False)
    is_available:      Mapped[bool]          = mapped_column(Boolean, default=True)
    rating:            Mapped[float]         = mapped_column(Float, default=0.0)
    total_reviews:     Mapped[int]           = mapped_column(Integer, default=0)
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id:           Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id:    Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    day_of_week:  Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon, 6=Sun
    start_time:   Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    end_time:     Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    slot_duration: Mapped[int] = mapped_column(Integer, default=30)        # minutes
    is_active:    Mapped[bool] = mapped_column(Boolean, default=True)


class DoctorReview(Base):
    __tablename__ = "doctor_reviews"

    id:           Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id:    Mapped[str]           = mapped_column(String(36), nullable=False, index=True)
    patient_id:   Mapped[str]           = mapped_column(String(36), nullable=False)
    appointment_id: Mapped[str]         = mapped_column(String(36), nullable=False)
    rating:       Mapped[int]           = mapped_column(Integer, nullable=False)  # 1-5
    comment:      Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
