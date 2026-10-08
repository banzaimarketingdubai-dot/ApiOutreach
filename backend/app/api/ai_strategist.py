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
