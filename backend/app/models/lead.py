import uuid
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    audience_id = Column(UUID(as_uuid=True), ForeignKey("audiences.id", ondelete="SET NULL"), nullable=True, index=True)
    
    company_name = Column(String, index=True, nullable=False)
    business_type = Column(String, index=True, nullable=True)
    city = Column(String, index=True, nullable=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    website = Column(String, index=True, nullable=True)
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    revo_score = Column(Integer, default=100)
    audit_notes = Column(Text, nullable=True)
    custom_data = Column(JSONB, default=dict) # Flexible LLM output JSON
    is_unsubscribed = Column(Boolean, default=False, index=True) # Unsubscribed from outreach
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="leads")
    audience = relationship("Audience", back_populates="leads")
    contacts = relationship("Contact", back_populates="lead", cascade="all, delete-orphan", lazy="selectin")
    email_sequences = relationship("EmailSequence", back_populates="lead", cascade="all, delete-orphan", lazy="selectin")
