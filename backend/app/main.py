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
from app.api.settings import router as settings_router
from app.api.templates import router as templates_router
from app.api.outreach import router as outreach_router

# Import models so Base.metadata is fully populated for create_all
import app.models.user
import app.models.lead
import app.models.contact
import app.models.outreach_campaign
import app.models.email_sequence


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            from sqlalchemy import text
            
            statements = [
                "ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS logs JSONB DEFAULT '[]'::jsonb;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_unsubscribed BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS funnel_type VARCHAR(100) DEFAULT 'EMPATHY_AUDIT';",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS current_touch INTEGER DEFAULT 1;",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS promo_status VARCHAR(50) DEFAULT 'INITIAL_AUDIT';",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS next_send_date TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS email_subject VARCHAR(255);",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS email_content TEXT;",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS opened_at TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS clicked_at TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE email_sequences ALTER COLUMN campaign_id DROP NOT NULL;"

            ]
            
            for stmt_text in statements:
                try:
                    await conn.execute(text(stmt_text))
                except Exception as stmt_err:
                    logger.warning(f"Migration statement skipped ({stmt_text}): {stmt_err}")

        
        # Postgres ALTER TYPE cannot run inside a transaction block
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            try:
                await conn.execute(text("ALTER TYPE campaignstatus ADD VALUE IF NOT EXISTS 'PAUSED';"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TYPE campaignstatus ADD VALUE IF NOT EXISTS 'CANCELLED';"))
            except Exception:
                pass
            
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
app.include_router(settings_router, prefix=f"{settings.API_V1_STR}/settings", tags=["Settings"])
app.include_router(templates_router, prefix=f"{settings.API_V1_STR}/templates", tags=["Templates"])
app.include_router(outreach_router, prefix=f"{settings.API_V1_STR}/outreach", tags=["Outreach"])

@app.get("/")
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }
