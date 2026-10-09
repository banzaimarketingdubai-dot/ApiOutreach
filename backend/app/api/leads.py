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

@router.get("/stats")
async def get_leads_stats(db: AsyncSession = Depends(get_db)):
    # Simple count of leads having specific contacts
    # Total
    total = await db.execute(select(func.count(Lead.id)))
    total_val = total.scalar_one()

    # WhatsApps
    wa = await db.execute(select(func.count(Lead.id)).where(Lead.contacts.any(Contact.contact_type == "whatsapp")))
    wa_val = wa.scalar_one()

    # Emails
    emails = await db.execute(select(func.count(Lead.id)).where(Lead.contacts.any(Contact.contact_type == "email")))
    email_val = emails.scalar_one()
    
    # Phones
    phones = await db.execute(select(func.count(Lead.id)).where(Lead.contacts.any(Contact.contact_type == "phone")))
    phone_val = phones.scalar_one()

    # Websites
    websites = await db.execute(select(func.count(Lead.id)).where(Lead.website != None))
    website_val = websites.scalar_one()

    return {
        "total": total_val,
        "whatsapp": wa_val,
        "email": email_val,
        "phone": phone_val,
        "website": website_val
    }

@router.get("", response_model=dict)
async def list_leads(
    niche: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    has_whatsapp: Optional[bool] = Query(None),
    has_email: Optional[bool] = Query(None),
    has_phone: Optional[bool] = Query(None),
    has_website: Optional[bool] = Query(None),
    min_score: Optional[int] = Query(None),
    min_rating: Optional[float] = Query(None),
    max_rating: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    campaign_id: Optional[UUID] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Lead)
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
    if min_rating is not None:
        filters.append(Lead.rating >= min_rating)
    if max_rating is not None:
        filters.append(Lead.rating <= max_rating)
    if campaign_id:
        filters.append(Lead.campaign_id == campaign_id)
    if search:
        filters.append(or_(
            Lead.company_name.ilike(f"%{search}%"),
            Lead.address.ilike(f"%{search}%"),
            Lead.website.ilike(f"%{search}%")
        ))

    if has_whatsapp is True:
        filters.append(Lead.contacts.any(Contact.contact_type == "whatsapp"))
    if has_email is True:
        filters.append(Lead.contacts.any(Contact.contact_type == "email"))
    if has_phone is True:
        filters.append(Lead.contacts.any(Contact.contact_type == "phone"))

    if filters:
        stmt = stmt.where(and_(*filters))

    # Apply sorting
    sort_column = getattr(Lead, sort_by, Lead.created_at)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(desc(sort_column))
    else:
        stmt = stmt.order_by(sort_column)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total_count = total_res.scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    res = await db.execute(stmt)
    leads = res.scalars().all()

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

@router.delete("/tools/clean_all", status_code=status.HTTP_204_NO_CONTENT)
async def clean_all_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.email != "admin@revo.ai":
        raise HTTPException(status_code=403, detail="Not authorized")
    from sqlalchemy import text
    await db.execute(text("TRUNCATE TABLE leads CASCADE"))
    await db.commit()

@router.post("/tools/enrich")
async def trigger_targeted_enrichment(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead_ids = body.get("lead_ids", [])
    if not lead_ids:
        raise HTTPException(status_code=400, detail="lead_ids array is required")
        
    # Set status to in_progress immediately
    from sqlalchemy import cast, String
    leads_res = await db.execute(select(Lead).where(cast(Lead.id, String).in_(lead_ids)))
    leads = leads_res.scalars().all()
    for l in leads:
        existing = l.custom_data or {}
        existing["enrichment_status"] = "in_progress"
        l.custom_data = existing
    await db.commit()
        
    from app.workers.enrichment_tasks import run_targeted_enrichment
    run_targeted_enrichment.delay(lead_ids, None)
    return {"status": "success", "message": f"Enrichment background task queued for {len(lead_ids)} leads"}

@router.get("/tools/duplicates", response_model=List[List[LeadResponse]])
async def get_suspected_duplicates(
    campaign_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import re
    stmt = select(Lead)
    if campaign_id:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
    res = await db.execute(stmt)
    all_leads = res.scalars().all()
    
    groups = {}
    stop_words = {"the", "a", "an", "and", "or", "of", "in", "to", "for"}
    for l in all_leads:
        if not l.company_name: continue
        words = [w.lower() for w in re.split(r'\W+', l.company_name) if w.lower() not in stop_words and len(w) > 1]
        
        # Priority 1: Phone match
        phone_val = re.sub(r'\D', '', l.phone) if l.phone else None
        
        # Priority 2: Name + City match
        if phone_val and len(phone_val) >= 7:
            key = f"phone:{phone_val}"
        else:
            first_two = " ".join(words[:2]) if len(words) >= 2 else (words[0] if words else l.company_name.lower())
            city_val = l.city.lower() if l.city else "unknown_city"
            key = f"name_city:{first_two}:{city_val}"
            
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
