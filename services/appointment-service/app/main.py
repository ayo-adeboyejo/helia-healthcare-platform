from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.redis import init_redis, close_redis
from app.core.logger import logger
from app.routes.appointments import router as appointment_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("appointment_service_starting")
    await init_db()
    await init_redis()
    logger.info(f"appointment_service_ready port={settings.port}")
    yield
    await close_redis()
    logger.info("appointment_service_stopped")


app = FastAPI(
    title="Helia Appointment Service",
    description="Appointment booking, scheduling and waitlist management",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointment_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "appointment-service", "version": "1.0.0"}
