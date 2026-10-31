from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_audience_icp: Optional[str] = None
    pain_points: Optional[List[str]] = []
    value_props: Optional[List[str]] = []
    target_action_cta: Optional[str] = None
    pricing_details: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}

class ProductCreate(ProductBase):
    project_id: UUID

class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    target_audience_icp: Optional[str] = None
    pain_points: Optional[List[str]] = None
    value_props: Optional[List[str]] = None
    target_action_cta: Optional[str] = None
    pricing_details: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ProductResponse(ProductBase):
    id: UUID
    project_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
