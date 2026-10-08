from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.campaign import CampaignStatus
from app.schemas.ai_strategist import CampaignConfigGenerated

class CampaignCreate(BaseModel):
    campaign_name: str
    target_geo: Optional[str] = None
    target_niches: List[str] = []
    ai_config: CampaignConfigGenerated

class CampaignUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    campaign_name: Optional[str] = None
    target_geo: Optional[str] = None
    target_niches: Optional[List[str]] = None
    status: Optional[CampaignStatus] = None
    ai_config: Optional[Dict[str, Any]] = None

class CampaignResponse(BaseModel):
    id: UUID
    campaign_name: str
    status: CampaignStatus
    target_geo: Optional[str] = None
    target_niches: List[str] = []
    ai_config: Dict[str, Any] = {}
    stats: Dict[str, Any] = {}
    error_log: Optional[str] = None
    logs: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
