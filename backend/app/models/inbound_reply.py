import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class ReplyIntent(str, enum.Enum):
    INTERESTED = "INTERESTED"       # Hot lead wanting demo/quote/meeting
    OBJECTION = "OBJECTION"         # Has a question, price concern or timing issue
    QUESTION = "QUESTION"           # Asking for details
    UNSUBSCRIBE = "UNSUBSCRIBE"     # "Unsubscribe me", "Not interested", "Stop"
    OUT_OF_OFFICE = "OUT_OF_OFFICE" # Autoresponder / Vacation
    NEUTRAL = "NEUTRAL"             # Other / Unclear

class InboundReply(Base):
    __tablename__ = "inbound_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("outreach_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    email_sequence_id = Column(UUID(as_uuid=True), ForeignKey("email_sequences.id", ondelete="SET NULL"), nullable=True)

    from_email = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    message_body = Column(Text, nullable=False)

    intent = Column(SQLEnum(ReplyIntent, native_enum=False), default=ReplyIntent.NEUTRAL, nullable=False, index=True)
    ai_analysis = Column(Text, nullable=True)         # Short summary of lead's objection/request
    ai_draft_response = Column(Text, nullable=True)   # Suggested reply prepared by AI

    is_handled = Column(Boolean, default=False, index=True)
    handled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    lead = relationship("Lead", lazy="selectin")
    project = relationship("Project", lazy="selectin")
    campaign = relationship("OutreachCampaign", lazy="selectin")
    email_sequence = relationship("EmailSequence", lazy="selectin")
