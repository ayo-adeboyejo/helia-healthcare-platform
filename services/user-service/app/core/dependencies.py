from fastapi import HTTPException, Header
from typing import Optional
import httpx
from app.config import settings


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ")[1]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.auth_service_url}/auth/verify-token",
                json={"token": token},
                timeout=10.0,
            )
        data = response.json()
        if not data.get("valid"):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return data
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")


async def require_doctor(current_user: dict = None) -> dict:
    if current_user.get("role") not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Doctor access required")
    return current_user


async def require_admin(current_user: dict = None) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
