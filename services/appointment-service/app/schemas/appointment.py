from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date


class AppointmentCreate(BaseModel):
    doctor_id:        str
    appointment_date: date
    start_time:       str  # HH:MM
    reason:           Optional[str] = None
    is_recurring:     bool = False
    frequency:        Optional[str] = None  # weekly | biweekly | monthly
    end_date:         Optional[date] = None

    @field_validator("start_time")
    @classmethod
    def valid_time(cls, v):
        try:
            h, m = v.split(":")
            assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        except Exception:
            raise ValueError("Time must be in HH:MM format")
        return v


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    start_time:       Optional[str]  = None
    status:           Optional[str]  = None
    notes:            Optional[str]  = None


class AppointmentResponse(BaseModel):
    id:               str
    patient_id:       str
    doctor_id:        str
    appointment_date: date
    start_time:       str
    end_time:         str
    status:           str
    reason:           Optional[str] = None
    notes:            Optional[str] = None
    consultation_fee: float
    is_recurring:     bool
    created_at:       datetime

    class Config:
        from_attributes = True


class WaitlistCreate(BaseModel):
    doctor_id:      str
    preferred_date: Optional[date] = None
    preferred_time: Optional[str]  = None


class WaitlistResponse(BaseModel):
    id:             str
    patient_id:     str
    doctor_id:      str
    preferred_date: Optional[date] = None
    preferred_time: Optional[str]  = None
    status:         str
    created_at:     datetime

    class Config:
        from_attributes = True


class AvailableSlotsRequest(BaseModel):
    doctor_id: str
    date:      date


class SlotResponse(BaseModel):
    time:      str
    available: bool
