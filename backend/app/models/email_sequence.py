import uuid
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class FunnelType(str, enum.Enum):
    HIDDEN_GEMS = "HIDDEN_GEMS"
    SINKING_GIANTS = "SINKING_GIANTS"
    GHOSTS = "GHOSTS"
    EMPATHY_AUDIT = "EMPATHY_AUDIT"
    CUSTOM = "CUSTOM"


class EmailSequenceStatus(str, enum.Enum):
    DRAFT = "DRAFT"         # Awaiting user approval
    QUEUED = "QUEUED"       # Approved, waiting for Celery to send
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SENT = "SENT"
    OPENED = "OPENED"
    REPLIED = "REPLIED"     # Hot Lead
    BOUNCED = "BOUNCED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    COMPLETED = "COMPLETED"

class PromoTrackStatus(str, enum.Enum):
    NONE = "NONE"
    CODE_SENT = "CODE_SENT"
    TRIAL_ACTIVE = "TRIAL_ACTIVE"
    CONVERTED = "CONVERTED"
    DROPPED = "DROPPED"
    UNSUBSCRIBED = "UNSUBSCRIBED"

class EmailSequence(Base):
    __tablename__ = "email_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=True)
    funnel_type = Column(SQLEnum(FunnelType, native_enum=False), default=FunnelType.CUSTOM, nullable=False, index=True)
    
    current_touch = Column(Integer, default=1) # Which step of the 5-touch funnel
    status = Column(SQLEnum(EmailSequenceStatus, native_enum=False), default=EmailSequenceStatus.DRAFT, nullable=False, index=True)
    promo_status = Column(SQLEnum(PromoTrackStatus, native_enum=False), default=PromoTrackStatus.NONE, nullable=False, index=True)
    
    next_send_date = Column(DateTime(timezone=True), nullable=True) # When to send the next email
    email_subject = Column(String, nullable=True)
    email_content = Column(Text, nullable=True) # The generated email body
    
    # Analytics tracking
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Optional relationships
    lead = relationship("Lead")
    campaign = relationship("OutreachCampaign")

class OutreachTemplate(Base):
    __tablename__ = "outreach_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    funnel_type = Column(SQLEnum(FunnelType, native_enum=False), nullable=False)
    touch_level = Column(Integer, nullable=False) # 1 to 5
    subject_template = Column(String, nullable=False)
    body_template = Column(Text, nullable=False)
    ai_prompt_context = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
