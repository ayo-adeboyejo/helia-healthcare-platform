from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.logger import logger
from app.routes.users import router as user_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("user_service_starting")
    await init_db()
    logger.info(f"user_service_ready port={settings.port}")
    yield
    logger.info("user_service_stopped")


app = FastAPI(
    title="Helia User Service",
    description="Patient and doctor profile management",
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

app.include_router(user_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "user-service", "version": "1.0.0"}
