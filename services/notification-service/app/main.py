from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import logger
from app.routes.notifications import router as notification_router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("notification_service_starting")
    logger.info(f"notification_service_ready port={settings.port} mode={settings.environment}")
    yield
    logger.info("notification_service_stopped")

app = FastAPI(title="Helia Notification Service", description="Email notifications via AWS SES", version="1.0.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(notification_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service", "version": "1.0.0"}
