from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine, Base
from app.api.auth import router as auth_router
from app.api.ai_strategist import router as ai_router
from app.api.campaigns import router as campaigns_router
from app.api.leads import router as leads_router
from app.api.tasks import router as tasks_router
from app.api.export import router as export_router
from app.api.apify import router as apify_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Database table initialization skipped/warning: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(ai_router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Strategist"])
app.include_router(campaigns_router, prefix=f"{settings.API_V1_STR}/campaigns", tags=["Campaigns"])
app.include_router(leads_router, prefix=f"{settings.API_V1_STR}/leads", tags=["Leads"])
app.include_router(tasks_router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Tasks"])
app.include_router(export_router, prefix=f"{settings.API_V1_STR}/export", tags=["Export"])
app.include_router(apify_router, prefix=f"{settings.API_V1_STR}/apify", tags=["Apify Account"])

@app.get("/")
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }
