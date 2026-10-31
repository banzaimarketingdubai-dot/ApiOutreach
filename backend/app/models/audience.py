import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Audience(Base):
    __tablename__ = "audiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String, default="PARSER", index=True) # PARSER, CSV_IMPORT, MANUAL, LEGACY
    stats = Column(JSONB, default=dict) # {"total_leads": 0, "with_email": 0, "with_phone": 0, "enriched": 0}
    custom_fields_schema = Column(JSONB, default=list) # [{field_key: "...", title: "...", description: "..."}]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="audiences")
    leads = relationship("Lead", back_populates="audience", cascade="all, delete-orphan", lazy="selectin")
    outreach_campaigns = relationship("OutreachCampaign", back_populates="audience")
