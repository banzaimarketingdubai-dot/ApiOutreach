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

    # Launch Celery background task
    try:
        run_campaign_scraping.delay(str(campaign.id))
    except Exception as e:
        # Fallback if Celery redis isn't connected synchronously
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
