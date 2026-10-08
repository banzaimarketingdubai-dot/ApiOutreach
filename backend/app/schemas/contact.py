from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.contact import ContactCategory

class ContactBase(BaseModel):
    contact_category: ContactCategory = ContactCategory.STANDARD
    contact_type: str
    contact_value: str
    source: str = "gmaps"
    is_primary: bool = False

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: UUID
    lead_id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
