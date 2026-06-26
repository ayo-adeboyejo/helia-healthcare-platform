from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class PatientCreate(BaseModel):
    user_id:       str
    first_name:    str
    last_name:     str
    date_of_birth: Optional[str] = None
    gender:        Optional[str] = None
    phone:         Optional[str] = None
    address:       Optional[str] = None
    blood_type:    Optional[str] = None
    allergies:     Optional[str] = None


class PatientUpdate(BaseModel):
    first_name:    Optional[str] = None
    last_name:     Optional[str] = None
    date_of_birth: Optional[str] = None
    gender:        Optional[str] = None
    phone:         Optional[str] = None
    address:       Optional[str] = None
    blood_type:    Optional[str] = None
    allergies:     Optional[str] = None


class PatientResponse(BaseModel):
    id:            str
    user_id:       str
    first_name:    str
    last_name:     str
    date_of_birth: Optional[str] = None
    gender:        Optional[str] = None
    phone:         Optional[str] = None
    address:       Optional[str] = None
    blood_type:    Optional[str] = None
    allergies:     Optional[str] = None
    avatar_url:    Optional[str] = None
    created_at:    datetime

    class Config:
        from_attributes = True


class SpecialtyCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    icon:        Optional[str] = None


class SpecialtyResponse(BaseModel):
    id:          str
    name:        str
    description: Optional[str] = None
    icon:        Optional[str] = None

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    user_id:          str
    first_name:       str
    last_name:        str
    specialty_id:     Optional[str] = None
    qualification:    Optional[str] = None
    experience_years: int = 0
    bio:              Optional[str] = None
    consultation_fee: float = 0.0
    languages:        Optional[str] = None
    phone:            Optional[str] = None
    clinic_address:   Optional[str] = None


class DoctorUpdate(BaseModel):
    first_name:       Optional[str]   = None
    last_name:        Optional[str]   = None
    specialty_id:     Optional[str]   = None
    qualification:    Optional[str]   = None
    experience_years: Optional[int]   = None
    bio:              Optional[str]   = None
    consultation_fee: Optional[float] = None
    languages:        Optional[str]   = None
    phone:            Optional[str]   = None
    clinic_address:   Optional[str]   = None
    is_available:     Optional[bool]  = None


class DoctorResponse(BaseModel):
    id:               str
    user_id:          str
    first_name:       str
    last_name:        str
    specialty_id:     Optional[str]   = None
    qualification:    Optional[str]   = None
    experience_years: int
    bio:              Optional[str]   = None
    consultation_fee: float
    languages:        Optional[str]   = None
    phone:            Optional[str]   = None
    clinic_address:   Optional[str]   = None
    avatar_url:       Optional[str]   = None
    is_approved:      bool
    is_available:     bool
    rating:           float
    total_reviews:    int
    created_at:       datetime

    class Config:
        from_attributes = True


class AvailabilitySlotCreate(BaseModel):
    doctor_id:     str
    day_of_week:   int  # 0=Monday, 6=Sunday
    start_time:    str  # HH:MM
    end_time:      str  # HH:MM
    slot_duration: int = 30

    @field_validator("day_of_week")
    @classmethod
    def valid_day(cls, v):
        if v not in range(7):
            raise ValueError("day_of_week must be 0-6")
        return v


class AvailabilitySlotResponse(BaseModel):
    id:            str
    doctor_id:     str
    day_of_week:   int
    start_time:    str
    end_time:      str
    slot_duration: int
    is_active:     bool

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    doctor_id:      str
    patient_id:     str
    appointment_id: str
    rating:         int
    comment:        Optional[str] = None

    @field_validator("rating")
    @classmethod
    def valid_rating(cls, v):
        if v not in range(1, 6):
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    id:             str
    doctor_id:      str
    patient_id:     str
    appointment_id: str
    rating:         int
    comment:        Optional[str] = None
    created_at:     datetime

    class Config:
        from_attributes = True
