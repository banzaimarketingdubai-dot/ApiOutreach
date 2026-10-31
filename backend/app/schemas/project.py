from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    reply_to_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}
    is_default: Optional[bool] = False

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    reply_to_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

class ProjectResponse(ProjectBase):
    id: UUID
    products_count: Optional[int] = 0
    audiences_count: Optional[int] = 0
    leads_count: Optional[int] = 0
    campaigns_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
