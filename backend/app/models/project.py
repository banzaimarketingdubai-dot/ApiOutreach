import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Default sender settings for this project
    sender_name = Column(String, nullable=True)
    sender_email = Column(String, nullable=True)
    reply_to_email = Column(String, nullable=True)
    
    # Project-level configurations (SMTP, Resend API key, Telegram alert settings, limits)
    settings = Column(JSONB, default=dict)
    is_default = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    products = relationship("Product", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    audiences = relationship("Audience", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    leads = relationship("Lead", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    outreach_campaigns = relationship("OutreachCampaign", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
