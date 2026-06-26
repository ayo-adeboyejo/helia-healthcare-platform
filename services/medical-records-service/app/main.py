from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.mongodb import init_mongodb, close_mongodb
from app.core.logger import logger
from app.routes.records import router as records_router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("medical_records_service_starting")
    await init_mongodb()
    logger.info(f"medical_records_service_ready port={settings.port}")
    yield
    await close_mongodb()
    logger.info("medical_records_service_stopped")

app = FastAPI(title="Helia Medical Records Service", description="Patient records, prescriptions and document storage", version="1.0.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(records_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "medical-records-service", "version": "1.0.0"}
