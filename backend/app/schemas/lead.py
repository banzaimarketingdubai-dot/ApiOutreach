from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.schemas.contact import ContactResponse, ContactCreate

class EmailSequenceBase(BaseModel):
    id: UUID
    funnel_type: str
    current_touch: int
    status: str
    
    class Config:
        from_attributes = True

class LeadBase(BaseModel):
    company_name: str
    business_type: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    rating: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    revo_score: Optional[int] = 100
    audit_notes: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = {}
    is_unsubscribed: Optional[bool] = False

class LeadCreate(LeadBase):
    project_id: Optional[UUID] = None
    audience_id: Optional[UUID] = None
    contacts: List[ContactCreate] = []

class LeadUpdate(BaseModel):
    project_id: Optional[UUID] = None
    audience_id: Optional[UUID] = None
    company_name: Optional[str] = None
    business_type: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    revo_score: Optional[int] = None
    audit_notes: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    is_unsubscribed: Optional[bool] = None

class LeadResponse(LeadBase):
    id: UUID
    project_id: Optional[UUID] = None
    audience_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    contacts: List[ContactResponse] = []
    email_sequences: List[EmailSequenceBase] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LeadFilter(BaseModel):
    project_id: Optional[UUID] = None
    audience_id: Optional[UUID] = None
    niche: Optional[str] = None
    city: Optional[str] = None
    has_whatsapp: Optional[bool] = None
    has_website: Optional[bool] = None
    min_score: Optional[int] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50
