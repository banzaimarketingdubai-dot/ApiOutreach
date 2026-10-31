import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    target_audience_icp = Column(Text, nullable=True)     # Ideal Customer Profile definition
    pain_points = Column(JSONB, default=list)             # List of pain points solved
    value_props = Column(JSONB, default=list)             # Key USPs / Value propositions
    target_action_cta = Column(String, nullable=True)     # Call to Action goal
    pricing_details = Column(Text, nullable=True)
    settings = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="products")
    outreach_campaigns = relationship("OutreachCampaign", back_populates="product")
