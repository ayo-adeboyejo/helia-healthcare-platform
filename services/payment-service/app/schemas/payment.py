from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentCreate(BaseModel):
    appointment_id: str
    doctor_id:      str
    amount:         float
    currency:       str = "GBP"
    payment_method: Optional[str] = None


class PaymentUpdate(BaseModel):
    status:         Optional[str]  = None
    payment_method: Optional[str]  = None
    notes:          Optional[str]  = None


class PaymentResponse(BaseModel):
    id:             str
    appointment_id: str
    patient_id:     str
    doctor_id:      str
    amount:         float
    currency:       str
    status:         str
    payment_method: Optional[str] = None
    paid_at:        Optional[datetime] = None
    created_at:     datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id:             str
    payment_id:     str
    patient_id:     str
    invoice_number: str
    amount:         float
    tax:            float
    total:          float
    status:         str
    issued_at:      datetime

    class Config:
        from_attributes = True


class DoctorEarningResponse(BaseModel):
    id:           str
    doctor_id:    str
    payment_id:   str
    amount:       float
    platform_fee: float
    net_amount:   float
    status:       str
    created_at:   datetime

    class Config:
        from_attributes = True


class RefundRequest(BaseModel):
    payment_id: str
    reason:     Optional[str] = None
