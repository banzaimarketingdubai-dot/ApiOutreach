from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, and_

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.lead import Lead
from app.models.contact import Contact
from app.schemas.lead import LeadResponse, LeadUpdate, LeadCreate
from app.services.entity_resolution import LeadMergerService

router = APIRouter()

@router.get("", response_model=dict)
async def list_leads(
    niche: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    has_whatsapp: Optional[bool] = Query(None),
    has_website: Optional[bool] = Query(None),
    min_score: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Lead).order_by(desc(Lead.created_at))
    filters = []

    if niche:
        filters.append(Lead.business_type.ilike(f"%{niche}%"))
    if city:
        filters.append(Lead.city.ilike(f"%{city}%"))
    if has_website is True:
        filters.append(and_(Lead.website.isnot(None), Lead.website != ""))
    elif has_website is False:
        filters.append(or_(Lead.website.is_(None), Lead.website == ""))
    if min_score is not None:
        filters.append(Lead.revo_score >= min_score)
    if search:
        filters.append(or_(
            Lead.company_name.ilike(f"%{search}%"),
            Lead.address.ilike(f"%{search}%"),
            Lead.website.ilike(f"%{search}%")
        ))

    if filters:
        stmt = stmt.where(and_(*filters))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total_count = total_res.scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    res = await db.execute(stmt)
    leads = res.scalars().all()

    # Filter WhatsApp in Python or via join if requested
    if has_whatsapp is not None:
        filtered_leads = []
        for lead in leads:
            wa_contacts = [c for c in lead.contacts if c.contact_type == "whatsapp"]
            if has_whatsapp and wa_contacts:
                filtered_leads.append(lead)
            elif not has_whatsapp and not wa_contacts:
                filtered_leads.append(lead)
        leads = filtered_leads

    lead_responses = [LeadResponse.model_validate(l) for l in leads]

    return {
        "items": lead_responses,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1
    }

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Lead).where(Lead.id == lead_id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    body: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Lead).where(Lead.id == lead_id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(lead, field, val)

    await db.commit()
    await db.refresh(lead)
    return lead

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Lead).where(Lead.id == lead_id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    await db.commit()
