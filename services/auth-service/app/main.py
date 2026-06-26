from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.redis import init_redis, close_redis
from app.core.logger import logger
from app.routes.auth import router as auth_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("auth_service_starting")
    await init_db()
    await init_redis()
    logger.info(f"auth_service_ready port={settings.port}")
    yield
    await close_redis()
    logger.info("auth_service_stopped")


app = FastAPI(
    title="Helia Auth Service",
    description="Authentication and authorisation for Helia",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service", "version": "1.0.0"}
