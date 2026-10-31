from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AudienceBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: Optional[str] = "PARSER"
    custom_fields_schema: Optional[List[Dict[str, Any]]] = []

class AudienceCreate(AudienceBase):
    project_id: UUID

class AudienceUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    source_type: Optional[str] = None
    custom_fields_schema: Optional[List[Dict[str, Any]]] = None

class AudienceResponse(AudienceBase):
    id: UUID
    project_id: UUID
    stats: Optional[Dict[str, Any]] = {}
    leads_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
