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
from app.api.users import router as users_router
from app.api.projects import router as projects_router
from app.api.products import router as products_router
from app.api.audiences import router as audiences_router
from app.api.funnels import router as funnels_router

# Import models so Base.metadata is fully populated for create_all
import app.models.user
import app.models.project
import app.models.product
import app.models.audience
import app.models.lead
import app.models.contact
import app.models.outreach_campaign
import app.models.email_sequence
import app.models.funnel
import app.models.inbound_reply

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
                "ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL;",
                "ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS audience_id UUID REFERENCES audiences(id) ON DELETE SET NULL;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS audience_id UUID REFERENCES audiences(id) ON DELETE SET NULL;",
                "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_unsubscribed BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE outreach_campaigns ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;",
                "ALTER TABLE outreach_campaigns ADD COLUMN IF NOT EXISTS product_id UUID REFERENCES products(id) ON DELETE SET NULL;",
                "ALTER TABLE outreach_campaigns ADD COLUMN IF NOT EXISTS audience_id UUID REFERENCES audiences(id) ON DELETE SET NULL;",
                "ALTER TABLE outreach_campaigns ADD COLUMN IF NOT EXISTS schedule_config JSONB DEFAULT '{}'::jsonb;",
                "ALTER TABLE outreach_campaigns ADD COLUMN IF NOT EXISTS is_manual_review_required BOOLEAN DEFAULT FALSE;",
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

            # Auto-seed Default Project & Default Audience for existing data
            try:
                import uuid
                proj_check = await conn.execute(text("SELECT id FROM projects WHERE is_default = TRUE LIMIT 1;"))
                default_proj_id = proj_check.scalar()
                if not default_proj_id:
                    proj_any = await conn.execute(text("SELECT id FROM projects ORDER BY created_at ASC LIMIT 1;"))
                    default_proj_id = proj_any.scalar()
                    if not default_proj_id:
                        default_proj_id = uuid.uuid4()
                        await conn.execute(
                            text("INSERT INTO projects (id, name, description, is_default, settings) VALUES (:id, :name, :desc, TRUE, '{}'::jsonb)"),
                            {"id": default_proj_id, "name": "Revo / GBPilot Master", "desc": "Default workspace migrated from v1"}
                        )
                    else:
                        await conn.execute(text("UPDATE projects SET is_default = TRUE WHERE id = :id"), {"id": default_proj_id})

                # Check default Audience
                aud_check = await conn.execute(text("SELECT id FROM audiences WHERE project_id = :proj_id LIMIT 1;"), {"proj_id": default_proj_id})
                default_aud_id = aud_check.scalar()
                if not default_aud_id:
                    default_aud_id = uuid.uuid4()
                    await conn.execute(
                        text("INSERT INTO audiences (id, project_id, name, description, source_type, stats) VALUES (:id, :proj_id, :name, :desc, 'LEGACY', '{}'::jsonb)"),
                        {"id": default_aud_id, "proj_id": default_proj_id, "name": "Master Database (Migrated)", "desc": "Initial migrated database"}
                    )

                # Backfill leads
                await conn.execute(
                    text("UPDATE leads SET project_id = :proj_id WHERE project_id IS NULL"),
                    {"proj_id": default_proj_id}
                )
                await conn.execute(
                    text("UPDATE leads SET audience_id = :aud_id WHERE audience_id IS NULL"),
                    {"aud_id": default_aud_id}
                )

                # Backfill campaigns
                await conn.execute(
                    text("UPDATE campaigns SET project_id = :proj_id WHERE project_id IS NULL"),
                    {"proj_id": default_proj_id}
                )
                await conn.execute(
                    text("UPDATE outreach_campaigns SET project_id = :proj_id WHERE project_id IS NULL"),
                    {"proj_id": default_proj_id}
                )
            except Exception as seed_err:
                logger.warning(f"Default project/audience seeding skipped: {seed_err}")

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
            try:
                await conn.execute(text("ALTER TYPE funneltype ADD VALUE IF NOT EXISTS 'EMPATHY_AUDIT';"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SUPER_ADMIN';"))
            except Exception:
                pass
            
            # Upgrade specific emails to SUPER_ADMIN
            try:
                await conn.execute(text("UPDATE users SET role = 'SUPER_ADMIN' WHERE email IN ('ceo@gbpilot.top', '0451611@gmail.com');"))
            except Exception as e:
                logger.warning(f"Failed to upgrade superadmins: {e}")
            
        logger.info("Database tables and multi-project schema initialized successfully.")

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
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(products_router, prefix=f"{settings.API_V1_STR}/products", tags=["Products"])
app.include_router(audiences_router, prefix=f"{settings.API_V1_STR}/audiences", tags=["Audiences"])
app.include_router(funnels_router, prefix=f"{settings.API_V1_STR}/funnels", tags=["Funnels"])
app.include_router(ai_router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Strategist"])
app.include_router(campaigns_router, prefix=f"{settings.API_V1_STR}/campaigns", tags=["Campaigns"])
app.include_router(leads_router, prefix=f"{settings.API_V1_STR}/leads", tags=["Leads"])
app.include_router(tasks_router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Tasks"])
app.include_router(export_router, prefix=f"{settings.API_V1_STR}/export", tags=["Export"])
app.include_router(apify_router, prefix=f"{settings.API_V1_STR}/apify", tags=["Apify Account"])
app.include_router(settings_router, prefix=f"{settings.API_V1_STR}/settings", tags=["Settings"])
app.include_router(templates_router, prefix=f"{settings.API_V1_STR}/templates", tags=["Templates"])
app.include_router(outreach_router, prefix=f"{settings.API_V1_STR}/outreach", tags=["Outreach"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])

@app.get("/")
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }
