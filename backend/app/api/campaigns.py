from typing import List
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
    logger = logging.getLogger(__name__)
    # Launch Celery background task
    try:
        run_campaign_scraping.delay(str(campaign.id))
        logger.info(f"Successfully queued celery task for campaign {campaign.id}")
    except Exception as e:
        logger.error(f"Failed to queue celery task: {e}")
        pass

    return campaign

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Campaign).order_by(desc(Campaign.created_at))
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
    
    if body.target_geo is not None:
        c.target_geo = body.target_geo
    if body.target_niches is not None:
        c.target_niches = body.target_niches
    if body.ai_config is not None:
        c.ai_config = {**c.ai_config, **body.ai_config}
    
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
    await db.commit()

    task = run_campaign_scraping.delay(str(c.id))
    return {"message": "Campaign pipeline launched", "task_id": task.id, "campaign_id": c.id}

async def _append_log(campaign, db, level: str, msg: str):
    from datetime import datetime
    log_entry = {"level": level, "message": msg, "timestamp": datetime.utcnow().isoformat() + "Z"}
    new_logs = list(campaign.logs) if campaign.logs else []
    new_logs.append(log_entry)
    campaign.logs = new_logs
    await db.commit()

@router.post("/{campaign_id}/pause")
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
    
    if c.status == CampaignStatus.RUNNING:
        c.status = CampaignStatus.PAUSED
        await _append_log(c, db, "warning", "Campaign paused by operator.")
    return {"status": c.status}

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
    return {"status": c.status}

@router.post("/{campaign_id}/stop")
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
    return {"status": c.status}

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
