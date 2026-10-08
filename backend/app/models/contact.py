import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class ContactCategory(str, enum.Enum):
    STANDARD = "STANDARD"
    NON_STANDARD = "NON_STANDARD"

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_category = Column(SQLEnum(ContactCategory), default=ContactCategory.STANDARD, nullable=False)
    contact_type = Column(String, index=True, nullable=False) # e.g. 'phone', 'email', 'whatsapp', 'telegram', 'instagram', 'facebook'
    contact_value = Column(String, nullable=False)
    source = Column(String, default="gmaps") # e.g. 'gmaps', '2gis', 'website', 'messenger_checker', 'manual'
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="contacts")
