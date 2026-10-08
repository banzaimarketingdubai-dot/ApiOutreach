from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ai_strategist import StrategyRequest, StrategyResponse, CampaignConfigGenerated
from app.services.ai_strategist import AIStrategistService

router = APIRouter()

@router.post("/strategy", response_model=StrategyResponse)
async def generate_campaign_strategy(
    body: StrategyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI Strategist Co-pilot endpoint:
    Takes a high-level outreach goal and generates an optimized campaign strategy JSON.
    """
    try:
        config_dict = await AIStrategistService.generate_campaign_config(
            user_goal=body.user_goal,
            geo=body.geo or "Dubai",
            additional_notes=body.additional_notes or ""
        )
        recommendation = CampaignConfigGenerated(**config_dict)
        return StrategyResponse(
            status="success",
            recommendation=recommendation,
            reasoning=config_dict.get("reasoning", "AI Strategist auto-generated recommended configuration based on niche potential.")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI strategy: {str(e)}")

from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.models.lead import Lead
from app.services.ai_enrichment import AIEnrichmentService
import uuid

class DryRunRequest(BaseModel):
    prompt_template: str
    lead_ids: List[str]

@router.post("/dry-run")
async def run_ai_dry_run(
    body: DryRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates AI generation for outreach templates on selected leads.
    """
    if not body.lead_ids:
        return {"results": []}
        
    stmt = select(Lead).where(Lead.id.in_([uuid.UUID(i) for i in body.lead_ids]))
    res = await db.execute(stmt)
    leads = res.scalars().all()
    
    # Convert leads to dict representation
    leads_data = []
    for l in leads:
        data = {
            "company_name": l.company_name,
            "city": l.city,
            "address": l.address,
            "website": l.website,
            "business_type": l.business_type,
            "custom_data": l.custom_data
        }
        leads_data.append(data)
        
    generated = await AIEnrichmentService.generate_dry_run_emails(body.prompt_template, leads_data)
    
    return {"results": [{"lead_name": l["company_name"], "generated_text": g} for l, g in zip(leads_data, generated)]}
