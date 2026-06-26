from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str
    role:     str = "patient"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v not in ("patient", "doctor", "admin"):
            raise ValueError("Role must be patient, doctor or admin")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int


class RefreshRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    token:        str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class VerifyTokenRequest(BaseModel):
    token: str


class VerifyTokenResponse(BaseModel):
    valid:   bool
    user_id: Optional[str] = None
    email:   Optional[str] = None
    role:    Optional[str] = None


class UserResponse(BaseModel):
    id:         str
    email:      str
    role:       str
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
