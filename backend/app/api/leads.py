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

@router.get("/tools/duplicates", response_model=List[List[LeadResponse]])
async def get_suspected_duplicates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Simple MVP duplicate detection: Group by first word of company_name in the same city
    res = await db.execute(select(Lead))
    all_leads = res.scalars().all()
    
    groups = {}
    for l in all_leads:
        if not l.company_name: continue
        key = (l.company_name.lower().split()[0], l.city)
        if key not in groups:
            groups[key] = []
        groups[key].append(l)
    
    dup_groups = [group for group in groups.values() if len(group) > 1]
    
    result = []
    for g in dup_groups:
        result.append([LeadResponse.model_validate(l) for l in g])
        
    return result

from pydantic import BaseModel
class MergeRequest(BaseModel):
    target_lead_id: UUID

@router.post("/{lead_id}/merge")
async def merge_lead(
    lead_id: UUID,
    body: MergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Source lead (to be deleted)
    src_res = await db.execute(select(Lead).where(Lead.id == lead_id))
    src_lead = src_res.scalars().first()
    
    # Target lead (to keep)
    tgt_res = await db.execute(select(Lead).where(Lead.id == body.target_lead_id))
    tgt_lead = tgt_res.scalars().first()
    
    if not src_lead or not tgt_lead:
        raise HTTPException(status_code=404, detail="Source or Target lead not found")
        
    # Merge fields (if target is empty)
    if not tgt_lead.website and src_lead.website: tgt_lead.website = src_lead.website
    if not tgt_lead.phone and src_lead.phone: tgt_lead.phone = src_lead.phone
    if not tgt_lead.address and src_lead.address: tgt_lead.address = src_lead.address
    
    # Re-assign contacts
    contact_res = await db.execute(select(Contact).where(Contact.lead_id == src_lead.id))
    contacts = contact_res.scalars().all()
    for c in contacts:
        c.lead_id = tgt_lead.id
        
    # Delete source
    await db.delete(src_lead)
    await db.commit()
    
    return {"message": "Merged successfully", "target_id": tgt_lead.id}
