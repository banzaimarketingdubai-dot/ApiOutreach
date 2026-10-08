from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class StrategyRequest(BaseModel):
    user_goal: str = Field(..., description="E.g., 'We want to sell CRM implementation to dental clinics in Dubai'")
    geo: Optional[str] = Field(default="Dubai", description="Target city or country")
    additional_notes: Optional[str] = None

class CustomVariableSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")
    key: str = Field(..., description="Snake_case key, e.g. has_online_booking")
    description: str = Field(..., description="Prompt instructions for LLM extraction")
    variable_type: str = Field(default="boolean", description="boolean, string, or list")

class CampaignConfigGenerated(BaseModel):
    model_config = ConfigDict(extra="ignore")
    campaign_name: str
    target_geo: str
    target_niches: List[str]
    search_queries: List[str]
    sources: List[str] = Field(default_factory=lambda: ["gmaps"])
    custom_variables: List[CustomVariableSpec]
    scoring_rules: Dict[str, Any] = Field(default_factory=lambda: {
        "missing_website_penalty": 10,
        "low_rating_penalty": 15,
        "low_reviews_penalty": 20
    })
    recommended_outreach_angle: Optional[str] = None
    reasoning: Optional[str] = None

class StrategyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str = "success"
    recommendation: CampaignConfigGenerated
    reasoning: str
