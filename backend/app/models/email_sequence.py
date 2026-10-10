import uuid
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class EmailSequenceStatus(str, enum.Enum):
    DRAFT = "DRAFT"         # Awaiting user approval
    QUEUED = "QUEUED"       # Approved, waiting for Celery to send
    SENT = "SENT"
    OPENED = "OPENED"
    REPLIED = "REPLIED"     # Hot Lead
    BOUNCED = "BOUNCED"

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
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="CASCADE"), nullable=False)
    
    current_touch = Column(Integer, default=1) # Which step of the 5-touch funnel
    status = Column(SQLEnum(EmailSequenceStatus, native_enum=False), default=EmailSequenceStatus.DRAFT, nullable=False, index=True)
    promo_status = Column(SQLEnum(PromoTrackStatus, native_enum=False), default=PromoTrackStatus.NONE, nullable=False, index=True)
    
    next_send_date = Column(DateTime(timezone=True), nullable=True) # When to send the next email
    email_subject = Column(String, nullable=True)
    email_content = Column(Text, nullable=True) # The generated email body
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Optional relationships
    lead = relationship("Lead")
    campaign = relationship("OutreachCampaign")
