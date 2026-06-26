import httpx
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings
from functools import lru_cache
import redis.asyncio as aioredis
import logging
import sys


class Settings(BaseSettings):
    environment:              str = "development"
    port:                     int = 8000
    redis_host:               str = "redis"
    redis_port:               int = 6379
    redis_password:           str
    auth_service_url:         str = "http://auth-service:8001"
    user_service_url:         str = "http://user-service:8002"
    appointment_service_url:  str = "http://appointment-service:8003"
    notification_service_url: str = "http://notification-service:8004"
    payment_service_url:      str = "http://payment-service:8005"
    medical_records_service_url: str = "http://medical-records-service:8006"
    search_service_url:       str = "http://search-service:8007"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

# Logger
logger = logging.getLogger("api-gateway")
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Redis client
redis_client = None

# Service route map
ROUTES = {
    "/auth":            settings.auth_service_url,
    "/users":           settings.user_service_url,
    "/patients":        settings.user_service_url,
    "/doctors":         settings.user_service_url,
    "/specialties":     settings.user_service_url,
    "/appointments":    settings.appointment_service_url,
    "/notifications":   settings.notification_service_url,
    "/payments":        settings.payment_service_url,
    "/medical-records": settings.medical_records_service_url,
    "/search":          settings.search_service_url,
}

# Routes that don't require authentication
PUBLIC_ROUTES = {
    ("POST", "/auth/register"),
    ("POST", "/auth/login"),
    ("POST", "/auth/verify-email"),
    ("POST", "/auth/forgot-password"),
    ("POST", "/auth/reset-password"),
    ("POST", "/auth/refresh"),
    ("GET",  "/doctors"),
    ("GET",  "/specialties"),
    ("GET",  "/search"),
    ("GET",  "/health"),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.from_url(
        f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/1",
        encoding="utf-8", decode_responses=True,
    )
    yield
    await redis_client.close()


app = FastAPI(
    title="Helia API Gateway",
    description="Single entry point for all Helia services",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_target_url(path: str) -> str:
    for prefix, target in ROUTES.items():
        if path.startswith(prefix):
            return target + path
    return None


def is_public(method: str, path: str) -> bool:
    for pub_method, pub_path in PUBLIC_ROUTES:
        if method == pub_method and path.startswith(pub_path):
            return True
    return False


async def rate_limit(client_ip: str, path: str) -> bool:
    key = f"rate:{client_ip}:{path}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 60)  # 60 second window
    return count > 100  # 100 requests per minute per IP


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    path   = request.url.path
    method = request.method

    # Skip gateway logic for health check
    if path == "/health":
        return await call_next(request)

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if await rate_limit(client_ip, path):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."}
        )

    # Auth check for protected routes
    if not is_public(method, path):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(status_code=401, content={"detail": "Authorization required"})

        try:
            async with httpx.AsyncClient() as client:
                verify_resp = await client.post(
                    f"{settings.auth_service_url}/auth/verify-token",
                    json={"token": auth_header.split(" ")[-1]},
                    timeout=5.0,
                )
            token_data = verify_resp.json()
            if not token_data.get("valid"):
                return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
        except httpx.RequestError:
            return JSONResponse(status_code=503, content={"detail": "Auth service unavailable"})

    return await call_next(request)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request):
    full_path  = f"/{path}"
    target_url = get_target_url(full_path)

    if not target_url:
        raise HTTPException(status_code=404, detail=f"No service found for path: {full_path}")

    try:
        body    = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=dict(request.query_params),
                headers=headers,
                content=body,
            )

        logger.info(f"{request.method} {full_path} → {response.status_code}")

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type"),
        )
    except httpx.RequestError as e:
        logger.error(f"Proxy error for {full_path}: {e}")
        raise HTTPException(status_code=502, detail="Service temporarily unavailable")


@app.get("/health")
async def health():
    return {
        "status":   "ok",
        "service":  "api-gateway",
        "services": {k: v for k, v in ROUTES.items()},
    }
