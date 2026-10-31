import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class FunnelSequence(Base):
    __tablename__ = "funnel_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    audience_id = Column(UUID(as_uuid=True), ForeignKey("audiences.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    tone_of_voice = Column(String, default="Professional & Empathetic")
    
    # List of touch steps: [{"step_number": 1, "step_name": "...", "delay_days": 0, "subject_template": "...", "body_template": "...", "target_cta": "..."}]
    steps = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    project = relationship("Project")
    product = relationship("Product")
    audience = relationship("Audience")
