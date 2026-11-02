from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.campaign import Campaign, CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate
from app.workers.scraping_tasks import run_campaign_scraping

router = APIRouter()

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = Campaign(
        project_id=body.project_id,
        audience_id=body.audience_id,
        campaign_name=body.campaign_name,
        target_geo=body.target_geo or body.ai_config.target_geo,
        target_niches=body.target_niches or body.ai_config.target_niches,
        ai_config=body.ai_config.model_dump(),
        status=CampaignStatus.PENDING,
        stats={"total_scraped": 0, "new_leads_created": 0, "merged_leads": 0}
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    import logging
    from datetime import datetime
    logger = logging.getLogger(__name__)
    # Launch Celery background task
    try:
        run_campaign_scraping.delay(str(campaign.id))
        logger.info(f"Successfully queued celery task for campaign {campaign.id}")
        init_log = {"level": "info", "message": "Запрос на парсинг отправлен в очередь Celery.", "timestamp": datetime.utcnow().isoformat() + "Z"}
        campaign.logs = [init_log]
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to queue celery task: {e}")
        warn_log = {"level": "warning", "message": f"Очередь задач Celery временно недоступна ({e}). Нажмите 'Запустить парсинг' для повтора.", "timestamp": datetime.utcnow().isoformat() + "Z"}
        campaign.logs = [warn_log]
        await db.commit()

    return campaign

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    project_id: Optional[UUID] = None,
    audience_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign)
    if project_id:
        stmt = stmt.where(Campaign.project_id == project_id)
    if audience_id:
        stmt = stmt.where(Campaign.audience_id == audience_id)
    stmt = stmt.order_by(desc(Campaign.created_at))
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c

@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    body: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if body.campaign_name is not None:
        c.campaign_name = body.campaign_name
    if body.target_geo is not None:
        c.target_geo = body.target_geo
    if body.target_niches is not None:
        c.target_niches = body.target_niches
    if body.ai_config is not None:
        c.ai_config = {**c.ai_config, **body.ai_config}
    if body.status is not None:
        c.status = body.status
    if body.project_id is not None:
        c.project_id = body.project_id
        from app.models.lead import Lead
        from sqlalchemy import update
        await db.execute(
            update(Lead).where(Lead.campaign_id == campaign_id).values(project_id=body.project_id)
        )
    if body.audience_id is not None:
        c.audience_id = body.audience_id
        from app.models.lead import Lead
        from sqlalchemy import update
        await db.execute(
            update(Lead).where(Lead.campaign_id == campaign_id).values(audience_id=body.audience_id)
        )
        try:
            from app.api.audiences import compute_audience_stats
            from app.models.audience import Audience
            aud_stats = await compute_audience_stats(db, body.audience_id)
            aud_res = await db.execute(select(Audience).where(Audience.id == body.audience_id))
            target_aud = aud_res.scalars().first()
            if target_aud:
                target_aud.stats = aud_stats
        except Exception as aud_err:
            logger.warning(f"Failed to update audience stats: {aud_err}")
    
    await _append_log(c, db, "info", "Campaign parameters updated on-the-fly.")
    await db.commit()
    await db.refresh(c)
    return c

@router.get("/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign.status, Campaign.stats, Campaign.logs).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Return only the last 20 logs for the live feed
    logs = row.logs if row.logs else []
    
    return {
        "status": row.status,
        "stats": row.stats or {},
        "logs": logs[-20:]
    }

@router.post("/{campaign_id}/start")
async def start_campaign_task(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    c.status = CampaignStatus.RUNNING
    await _append_log(c, db, "info", "Оператор запустил выполнение парсинга.")
    await db.commit()

    task_id = None
    try:
        task = run_campaign_scraping.delay(str(c.id))
        task_id = task.id
    except Exception as e:
        logger.error(f"Failed to queue task via celery: {e}")
        await _append_log(c, db, "error", f"Ошибка отправки задачи в Celery: {e}")

    return {"message": "Campaign pipeline launched", "task_id": task_id, "campaign_id": c.id}

async def _append_log(campaign, db, level: str, msg: str):
    from datetime import datetime
    log_entry = {"level": level, "message": msg, "timestamp": datetime.utcnow().isoformat() + "Z"}
    new_logs = list(campaign.logs) if campaign.logs else []
    new_logs.append(log_entry)
    campaign.logs = new_logs
    await db.commit()

@router.post("/{campaign_id}/suspend")
async def pause_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        if c.status == CampaignStatus.RUNNING:
            c.status = CampaignStatus.PAUSED
            await _append_log(c, db, "warning", "Campaign paused by operator.")
        return {"status": getattr(c.status, "value", c.status)}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.post("/tools/migrate_kyiv")
async def migrate_kyiv(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update, or_
    from app.models.lead import Lead
    
    # Check if Campaign "Beauty Kyiv" exists
    result = await db.execute(select(Campaign).where(Campaign.campaign_name == "Beauty Kyiv"))
    kyiv_camp = result.scalars().first()
    
    if not kyiv_camp:
        kyiv_camp = Campaign(
            campaign_name="Beauty Kyiv",
            status=CampaignStatus.PENDING,
            ai_config={
                "custom_variables": [
                    {"key": "has_online_booking", "description": "Does the site have online booking?"},
                    {"key": "uses_crm_chat", "description": "Does the site use WhatsApp or Live Chat widget?"}
                ]
            }
        )
        db.add(kyiv_camp)
        await db.commit()
        await db.refresh(kyiv_camp)
        
    stmt = update(Lead).where(
        or_(
            Lead.city.ilike("%Kyiv%"),
            Lead.address.ilike("%Kyiv%"),
            Lead.address.ilike("%Київ%")
        )
    ).values(campaign_id=kyiv_camp.id)
    
    res = await db.execute(stmt)
    await db.commit()
    return {"message": f"Successfully moved {res.rowcount} leads to Beauty Kyiv", "campaign_id": kyiv_camp.id}

@router.post("/tools/reset_stuck")
async def reset_stuck_leads(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.lead import Lead
    from sqlalchemy.orm.attributes import flag_modified
    
    # Assuming custom_data is a JSONB column
    stmt = select(Lead)
    res = await db.execute(stmt)
    leads = res.scalars().all()
    
    count = 0
    for lead in leads:
        if lead.custom_data and lead.custom_data.get("enrichment_status") == "in_progress":
            existing = dict(lead.custom_data)
            existing["enrichment_status"] = "none"
            lead.custom_data = existing
            flag_modified(lead, "custom_data")
            count += 1
            
    await db.commit()
    return {"message": f"Reset {count} stuck leads back to none"}

@router.post("/tools/fix_dubai_kyiv_geo")
async def fix_dubai_kyiv_geo(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update
    from app.models.lead import Lead
    
    stmt = update(Lead).where(
        Lead.city.ilike("%Dubai%") & 
        (Lead.address.ilike("%Kyiv%") | Lead.address.ilike("%Київ%"))
    ).values(city="Kyiv")
    
    res = await db.execute(stmt)
    await db.commit()
    
    return {"message": f"Fixed GEO for {res.rowcount} leads from Dubai to Kyiv"}

@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if c.status == CampaignStatus.PAUSED:
        c.status = CampaignStatus.RUNNING
        await _append_log(c, db, "info", "Campaign resumed by operator.")
    return {"status": c.status.value}

@router.post("/{campaign_id}/halt")
async def stop_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if c.status in [CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.PENDING]:
        c.status = CampaignStatus.CANCELLED
        await _append_log(c, db, "error", "Campaign emergency stopped by operator.")
    return {"status": c.status.value}

@router.post("/{campaign_id}/retry-failed")
async def retry_failed_batches(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    from app.workers.enrichment_tasks import run_campaign_enrichment
    run_campaign_enrichment.delay(str(c.id))
    await _append_log(c, db, "info", "Retry requested. Re-running enrichment phase.")
    return {"status": "Enrichment retried"}

from pydantic import BaseModel
class RecalculateScoreRequest(BaseModel):
    scoring_rules: dict

@router.post("/{campaign_id}/recalculate-score")
async def recalculate_score(
    campaign_id: UUID,
    body: RecalculateScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update rules
    c.ai_config = {**c.ai_config, "scoring_rules": body.scoring_rules}
    
    # Recalculate all leads in campaign synchronously for MVP
    from app.models.lead import Lead
    from app.services.scoring import calculate_revo_score_and_audit
    
    leads_res = await db.execute(select(Lead).where(Lead.campaign_id == campaign_id))
    leads = leads_res.scalars().all()
    
    for lead in leads:
        has_web = bool(lead.website)
        has_phone = bool(lead.phone)
        score, audit_notes = calculate_revo_score_and_audit(
            rating=lead.rating or 0.0,
            reviews_count=lead.reviews_count or 0,
            has_website=has_web,
            has_phone=has_phone,
            scoring_rules=body.scoring_rules
        )
        lead.revo_score = score
        lead.audit_notes = audit_notes
        
    await _append_log(c, db, "success", f"Mass recalculated scores for {len(leads)} leads.")
    await db.commit()
    return {"message": "Scores recalculated", "updated_leads": len(leads)}

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    res = await db.execute(stmt)
    c = res.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    await db.delete(c)
    await db.commit()
    return {"message": "Campaign deleted successfully"}
