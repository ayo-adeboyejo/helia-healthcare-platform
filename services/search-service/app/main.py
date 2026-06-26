from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.elasticsearch import init_elasticsearch, close_elasticsearch
from app.core.logger import logger
from app.routes.search import router as search_router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("search_service_starting")
    await init_elasticsearch()
    logger.info(f"search_service_ready port={settings.port}")
    yield
    await close_elasticsearch()
    logger.info("search_service_stopped")

app = FastAPI(title="Helia Search Service", description="Doctor discovery and search using Elasticsearch", version="1.0.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(search_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "search-service", "version": "1.0.0"}
