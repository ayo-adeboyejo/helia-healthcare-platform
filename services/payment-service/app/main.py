from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.logger import logger
from app.routes.payments import router as payment_router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("payment_service_starting")
    await init_db()
    logger.info(f"payment_service_ready port={settings.port}")
    yield
    logger.info("payment_service_stopped")

app = FastAPI(title="Helia Payment Service", description="Payment processing and invoicing", version="1.0.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(payment_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "payment-service", "version": "1.0.0"}
