import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.funnel import FunnelSequence
from app.models.project import Project
from app.models.product import Product
from app.models.audience import Audience
from app.models.lead import Lead
from app.services.ai_funnel import AIFunnelService

router = APIRouter()

class FunnelStepSchema(BaseModel):
    step_number: int
    step_name: Optional[str] = "Touch Step"
    delay_days: int = 0
    subject_template: str
    subject_variants: Optional[List[str]] = []
    body_template: str
    rationale: Optional[str] = None
    target_cta: Optional[str] = None

class FunnelCreate(BaseModel):
    project_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    audience_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    tone_of_voice: Optional[str] = "Professional & Empathetic"
    steps: List[FunnelStepSchema]

class FunnelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tone_of_voice: Optional[str] = None
    steps: Optional[List[FunnelStepSchema]] = None
    is_active: Optional[bool] = None

class FunnelResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    audience_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    tone_of_voice: Optional[str] = None
    steps: List[Dict[str, Any]] = []
    is_active: bool = True

    class Config:
        from_attributes = True

class AIGenerateFunnelRequest(BaseModel):
    product_id: uuid.UUID
    audience_id: uuid.UUID
    touches_count: int = 3
    tone_of_voice: Optional[str] = "Деловой и эмпатичный"
    custom_instructions: Optional[str] = None

class RenderPreviewRequest(BaseModel):
    subject_template: str
    body_template: str
    lead_id: uuid.UUID

@router.get("", response_model=List[FunnelResponse])
async def list_funnels(
    project_id: Optional[uuid.UUID] = Query(None),
    product_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List saved funnel sequences, optionally filtered by project or product."""
    stmt = select(FunnelSequence)
    if project_id:
        stmt = stmt.where(FunnelSequence.project_id == project_id)
    if product_id:
        stmt = stmt.where(FunnelSequence.product_id == product_id)
    stmt = stmt.order_by(FunnelSequence.created_at.desc())

    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=FunnelResponse, status_code=status.HTTP_201_CREATED)
async def create_funnel(
    data: FunnelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save an AI or customized sequence as a reusable funnel template."""
    proj = (await db.execute(select(Project).where(Project.id == data.project_id))).scalars().first()
    if not proj:
        raise HTTPException(status_code=400, detail="Project not found")

    new_funnel = FunnelSequence(
        project_id=data.project_id,
        product_id=data.product_id,
        audience_id=data.audience_id,
        name=data.name,
        description=data.description,
        tone_of_voice=data.tone_of_voice or "Professional & Empathetic",
        steps=[s.model_dump() for s in data.steps]
    )
    db.add(new_funnel)
    await db.commit()
    await db.refresh(new_funnel)
    return new_funnel

@router.get("/{funnel_id}", response_model=FunnelResponse)
async def get_funnel(
    funnel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get funnel sequence details."""
    stmt = select(FunnelSequence).where(FunnelSequence.id == funnel_id)
    funnel = (await db.execute(stmt)).scalars().first()
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel sequence not found")
    return funnel

@router.put("/{funnel_id}", response_model=FunnelResponse)
async def update_funnel(
    funnel_id: uuid.UUID,
    data: FunnelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update funnel steps or metadata."""
    stmt = select(FunnelSequence).where(FunnelSequence.id == funnel_id)
    funnel = (await db.execute(stmt)).scalars().first()
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel sequence not found")

    if data.name is not None:
        funnel.name = data.name
    if data.description is not None:
        funnel.description = data.description
    if data.tone_of_voice is not None:
        funnel.tone_of_voice = data.tone_of_voice
    if data.steps is not None:
        funnel.steps = [s.model_dump() for s in data.steps]
    if data.is_active is not None:
        funnel.is_active = data.is_active

    await db.commit()
    await db.refresh(funnel)
    return funnel

@router.delete("/{funnel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_funnel(
    funnel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a funnel sequence."""
    stmt = select(FunnelSequence).where(FunnelSequence.id == funnel_id)
    funnel = (await db.execute(stmt)).scalars().first()
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel sequence not found")

    await db.delete(funnel)
    await db.commit()
    return None

@router.post("/ai-generate")
async def generate_ai_funnel(
    body: AIGenerateFunnelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an N-touch cold outreach funnel tailored to a specific Product and Audience using Gemini/Grok.
    """
    prod = (await db.execute(select(Product).where(Product.id == body.product_id))).scalars().first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    aud = (await db.execute(select(Audience).where(Audience.id == body.audience_id))).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    product_dict = {
        "name": prod.name,
        "description": prod.description,
        "target_audience_icp": prod.target_audience_icp,
        "pain_points": prod.pain_points or [],
        "value_props": prod.value_props or [],
        "target_action_cta": prod.target_action_cta,
        "pricing_details": prod.pricing_details
    }

    audience_dict = {
        "name": aud.name,
        "description": aud.description,
        "source_type": aud.source_type,
        "custom_fields_schema": aud.custom_fields_schema or []
    }

    result = await AIFunnelService.generate_funnel_sequence(
        product_info=product_dict,
        audience_info=audience_dict,
        touches_count=body.touches_count,
        tone_of_voice=body.tone_of_voice or "Деловой и эмпатичный",
        custom_instructions=body.custom_instructions or ""
    )

    return result

@router.post("/render-preview")
async def render_email_preview(
    body: RenderPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Live render email subject and body replacing {{placeholders}} with real data of a lead.
    """
    lead = (await db.execute(select(Lead).where(Lead.id == body.lead_id))).scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_dict = {
        "company_name": lead.company_name,
        "city": lead.city,
        "address": lead.address,
        "website": lead.website,
        "business_type": lead.business_type,
        "rating": lead.rating,
        "revo_score": lead.revo_score,
        "custom_data": lead.custom_data or {}
    }

    rendered = AIFunnelService.render_preview(body.subject_template, body.body_template, lead_dict)
    return rendered
