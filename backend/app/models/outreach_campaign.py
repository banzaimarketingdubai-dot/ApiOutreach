import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class OutreachStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    audience_id = Column(UUID(as_uuid=True), ForeignKey("audiences.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String, index=True, nullable=False)
    prompt_template = Column(Text, nullable=True) # Custom prompt context for AI Funnel
    status = Column(SQLEnum(OutreachStatus, native_enum=False), default=OutreachStatus.DRAFT, nullable=False)
    filters = Column(JSONB, default=dict) # Audience targeting filters / subsegment criteria
    
    schedule_config = Column(JSONB, default=dict) # {"send_start_hour": 9, "send_end_hour": 18, "workdays_only": true, "daily_limit": 50, "delay_between_emails_sec": 120}
    is_manual_review_required = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="outreach_campaigns")
    product = relationship("Product", back_populates="outreach_campaigns")
    audience = relationship("Audience", back_populates="outreach_campaigns")
    email_sequences = relationship("EmailSequence", back_populates="campaign", cascade="all, delete-orphan", lazy="selectin")
