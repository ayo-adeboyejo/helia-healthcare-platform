import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from redis.asyncio import Redis
from typing import Optional

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.logger import logger
from app.models.user import User, RefreshToken, PasswordResetToken
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    ResetPasswordRequest, VerifyTokenRequest, VerifyTokenResponse,
    UserResponse, MessageResponse,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def utcnow():
    return datetime.now(timezone.utc)


# ── Register ──────────────────────────────────────────────────────────────────
@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"user_registered user_id={user.id} role={user.role}")
    return {"message": "Registration successful. You can now log in."}


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Rate limiting — 5 failed attempts locks for 15 minutes
    rate_key = f"login_attempts:{payload.email}"
    attempts = await redis.get(rate_key)
    if attempts and int(attempts) >= 5:
        ttl = await redis.ttl(rate_key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {ttl // 60} minutes."
        )

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password):
        pipe = redis.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 900)
        await pipe.execute()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Clear failed attempts on successful login
    await redis.delete(rate_key)

    token_data    = {"sub": user.id, "email": user.email, "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(rt)
    await db.commit()

    logger.info(f"user_login user_id={user.id}")
    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "expires_in":    settings.jwt_access_token_expire_minutes * 60,
    }


# ── Refresh token ─────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == payload.refresh_token,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > utcnow(),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")

    # Rotate — revoke old, issue new
    await db.execute(
        update(RefreshToken).where(RefreshToken.id == stored.id).values(revoked=True)
    )

    token_data  = {"sub": decoded["sub"], "email": decoded["email"], "role": decoded["role"]}
    new_access  = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    rt = RefreshToken(
        user_id=decoded["sub"],
        token=new_refresh,
        expires_at=utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(rt)
    await db.commit()

    return {
        "access_token":  new_access,
        "refresh_token": new_refresh,
        "token_type":    "bearer",
        "expires_in":    settings.jwt_access_token_expire_minutes * 60,
    }


# ── Logout ────────────────────────────────────────────────────────────────────
@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    decoded = decode_token(payload.refresh_token)
    if decoded:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token == payload.refresh_token)
            .values(revoked=True)
        )
        # Blacklist the refresh token
        ttl = max(0, int((datetime.fromtimestamp(decoded["exp"], tz=timezone.utc) - utcnow()).total_seconds()))
        if ttl > 0:
            await redis.setex(f"blacklist:{payload.refresh_token}", ttl, "1")
        await db.commit()

    logger.info("user_logout")
    return {"message": "Logged out successfully"}


# ── Reset password (token generated via admin or support flow) ────────────────
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > utcnow(),
        )
    )
    prt = result.scalar_one_or_none()
    if not prt:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    await db.execute(
        update(User)
        .where(User.id == prt.user_id)
        .values(password=hash_password(payload.new_password), updated_at=utcnow())
    )
    await db.execute(
        update(PasswordResetToken).where(PasswordResetToken.id == prt.id).values(used=True)
    )
    await db.commit()

    logger.info(f"password_reset user_id={prt.user_id}")
    return {"message": "Password reset successfully. You can now log in."}


# ── Verify token — called internally by all other services ────────────────────
@router.post("/verify-token", response_model=VerifyTokenResponse)
async def verify_token(
    payload: VerifyTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Check blacklist first — fast Redis lookup
    blacklisted = await redis.get(f"blacklist:{payload.token}")
    if blacklisted:
        return {"valid": False}

    decoded = decode_token(payload.token)
    if not decoded or decoded.get("type") != "access":
        return {"valid": False}

    result = await db.execute(select(User).where(User.id == decoded["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return {"valid": False}

    return {
        "valid":   True,
        "user_id": user.id,
        "email":   user.email,
        "role":    user.role,
    }


# ── Get current user profile ──────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.split(" ")[1]

    blacklisted = await redis.get(f"blacklist:{token}")
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    decoded = decode_token(token)
    if not decoded or decoded.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == decoded["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
