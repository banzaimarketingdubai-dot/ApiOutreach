from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.schemas.contact import ContactResponse, ContactCreate

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

class LeadCreate(LeadBase):
    contacts: List[ContactCreate] = []

class LeadUpdate(BaseModel):
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

class LeadResponse(LeadBase):
    id: UUID
    campaign_id: Optional[UUID] = None
    contacts: List[ContactResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LeadFilter(BaseModel):
    niche: Optional[str] = None
    city: Optional[str] = None
    has_whatsapp: Optional[bool] = None
    has_website: Optional[bool] = None
    min_score: Optional[int] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50
