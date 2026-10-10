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
    wa = await db.execute(select(func.count(Lead.id)).where(
        or_(
            Lead.contacts.any(Contact.contact_type == "whatsapp"),
            Lead.custom_data['whatsapp_available'].astext == 'true'
        )
    ))
    wa_val = wa.scalar_one()

    # Telegrams
    tg = await db.execute(select(func.count(Lead.id)).where(
        or_(
            Lead.contacts.any(Contact.contact_type == "telegram"),
            Lead.custom_data['telegram_available'].astext == 'true'
        )
    ))
    tg_val = tg.scalar_one()

    # Vibers
    vb = await db.execute(select(func.count(Lead.id)).where(
        or_(
            Lead.contacts.any(Contact.contact_type == "viber"),
            Lead.custom_data['viber_available'].astext == 'true'
        )
    ))
    vb_val = vb.scalar_one()

    # Emails
    emails = await db.execute(select(func.count(Lead.id)).where(Lead.contacts.any(Contact.contact_type == "email")))
    email_val = emails.scalar_one()
    
    # Phones
    phones = await db.execute(select(func.count(Lead.id)).where(Lead.contacts.any(Contact.contact_type == "phone")))
    phone_val = phones.scalar_one()

    # Websites
    websites = await db.execute(select(func.count(Lead.id)).where(Lead.website != None))
    website_val = websites.scalar_one()

    # Enrichment Stats
    from sqlalchemy import cast, String
    # Look into JSONB custom_data field
    enrich_prog = await db.execute(select(func.count(Lead.id)).where(
        Lead.custom_data['enrichment_status'].astext == 'in_progress'
    ))
    enrich_prog_val = enrich_prog.scalar_one()

    enrich_comp = await db.execute(select(func.count(Lead.id)).where(
        Lead.custom_data['enrichment_status'].astext == 'completed'
    ))
    enrich_comp_val = enrich_comp.scalar_one()

    enrich_fail = await db.execute(select(func.count(Lead.id)).where(
        Lead.custom_data['enrichment_status'].astext == 'failed'
    ))
    enrich_fail_val = enrich_fail.scalar_one()

    return {
        "total": total_val,
        "whatsapp": wa_val,
        "telegram": tg_val,
        "viber": vb_val,
        "email": email_val,
        "phone": phone_val,
        "website": website_val,
        "enrichment_in_progress": enrich_prog_val,
        "enrichment_completed": enrich_comp_val,
        "enrichment_failed": enrich_fail_val
    }

def apply_lead_filters(stmt, filters_dict: dict = None):
    if not filters_dict:
        return stmt
    from sqlalchemy import and_, or_
    filters = []

    
    niche = filters_dict.get("niche")
    city = filters_dict.get("city")
    has_website = filters_dict.get("has_website")
    min_score = filters_dict.get("min_score")
    min_rating = filters_dict.get("min_rating")
    max_rating = filters_dict.get("max_rating")
    campaign_id = filters_dict.get("campaign_id")
    search = filters_dict.get("search")
    has_whatsapp = filters_dict.get("has_whatsapp")
    has_telegram = filters_dict.get("has_telegram")
    has_viber = filters_dict.get("has_viber")
    has_email = filters_dict.get("has_email")
    has_phone = filters_dict.get("has_phone")
    enrichment_status = filters_dict.get("enrichment_status")

    if niche: filters.append(Lead.business_type.ilike(f"%{niche}%"))
    if city: filters.append(Lead.city.ilike(f"%{city}%"))
    if has_website is True: filters.append(and_(Lead.website.isnot(None), Lead.website != ""))
    elif has_website is False: filters.append(or_(Lead.website.is_(None), Lead.website == ""))
    def _to_int(val):
        try:
            return int(val) if val is not None and not str(val).startswith("FastAPI") and not hasattr(val, 'default') else None
        except (ValueError, TypeError):
            return None

    def _to_float(val):
        try:
            return float(val) if val is not None and not str(val).startswith("FastAPI") and not hasattr(val, 'default') else None
        except (ValueError, TypeError):
            return None

    min_score_val = _to_int(min_score)
    min_rating_val = _to_float(min_rating)
    max_rating_val = _to_float(max_rating)

    if min_score_val is not None: filters.append(Lead.revo_score >= min_score_val)
    if min_rating_val is not None: filters.append(Lead.rating >= min_rating_val)
    if max_rating_val is not None: filters.append(Lead.rating <= max_rating_val)
    if campaign_id and not hasattr(campaign_id, 'default'): filters.append(Lead.campaign_id == campaign_id)
    if search and isinstance(search, str) and search.strip(): filters.append(or_(Lead.company_name.ilike(f"%{search}%"), Lead.address.ilike(f"%{search}%"), Lead.website.ilike(f"%{search}%")))


    if has_whatsapp is True: 
        filters.append(or_(
            Lead.contacts.any(Contact.contact_type == "whatsapp"),
            Lead.custom_data['whatsapp_available'].astext == 'true'
        ))
    if has_telegram is True: 
        filters.append(or_(
            Lead.contacts.any(Contact.contact_type == "telegram"),
            Lead.custom_data['telegram_available'].astext == 'true'
        ))
    if has_viber is True: 
        filters.append(or_(
            Lead.contacts.any(Contact.contact_type == "viber"),
            Lead.custom_data['viber_available'].astext == 'true'
        ))
    if has_email is True: filters.append(Lead.contacts.any(Contact.contact_type == "email"))
    if has_phone is True: filters.append(Lead.contacts.any(Contact.contact_type == "phone"))

    if enrichment_status:
        from sqlalchemy import cast, String, or_
        if enrichment_status == "none":
            filters.append(or_(
                Lead.custom_data.is_(None),
                Lead.custom_data['enrichment_status'].astext.is_(None),
                Lead.custom_data['enrichment_status'].astext == ""
            ))
        else:
            filters.append(Lead.custom_data['enrichment_status'].astext == enrichment_status)
        
    if filters:
        stmt = stmt.where(and_(*filters))
    return stmt

@router.get("", response_model=dict)
async def list_leads(
    niche: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    has_whatsapp: Optional[bool] = Query(None),
    has_telegram: Optional[bool] = Query(None),
    has_viber: Optional[bool] = Query(None),
    has_email: Optional[bool] = Query(None),
    has_phone: Optional[bool] = Query(None),
    has_website: Optional[bool] = Query(None),
    min_score: Optional[int] = Query(None),
    min_rating: Optional[float] = Query(None),
    max_rating: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    enrichment_status: Optional[str] = Query(None),
    campaign_id: Optional[UUID] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        from sqlalchemy.orm import selectinload
        
        filters_dict = {
            "niche": niche, "city": city, "has_website": has_website,
            "min_score": min_score, "min_rating": min_rating, "max_rating": max_rating,
            "search": search, "campaign_id": campaign_id,
            "has_whatsapp": has_whatsapp, "has_telegram": has_telegram, "has_viber": has_viber,
            "has_email": has_email, "has_phone": has_phone,
            "enrichment_status": enrichment_status
        }

        # 1. Count total
        count_stmt = select(func.count(Lead.id))
        count_stmt = apply_lead_filters(count_stmt, filters_dict)
        total_res = await db.execute(count_stmt)
        total_count = total_res.scalar_one()

        # 2. Main query with selectinload & sorting
        stmt = select(Lead).options(
            selectinload(Lead.contacts),
            selectinload(Lead.email_sequences)
        )
        stmt = apply_lead_filters(stmt, filters_dict)


        sort_by_str = sort_by if isinstance(sort_by, str) else "created_at"
        sort_order_str = sort_order if isinstance(sort_order, str) else "desc"
        sort_column = getattr(Lead, sort_by_str, Lead.created_at)

        if sort_order_str.lower() == "desc":
            stmt = stmt.order_by(desc(sort_column), desc(Lead.id))
        else:
            stmt = stmt.order_by(sort_column, desc(Lead.id))

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
    except Exception as err:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(err)}")


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import selectinload
    stmt = select(Lead).options(
        selectinload(Lead.contacts),
        selectinload(Lead.email_sequences)
    ).where(Lead.id == lead_id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("", response_model=LeadResponse)
async def create_lead(
    body: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create lead
    lead_data = body.model_dump(exclude={"contacts"})
    lead = Lead(**lead_data)
    db.add(lead)
    await db.flush()
    
    # Create contacts
    for contact_data in body.contacts:
        contact = Contact(lead_id=lead.id, **contact_data.model_dump())
        db.add(contact)
        
    await db.commit()
    await db.refresh(lead)
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

@router.post("/tools/assign_all")
async def assign_all_leads(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.email != "admin@revo.ai":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    campaign_id = body.get("campaign_id")
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")
        
    # Assign all leads that don't have a campaign (or all leads) to this campaign
    from sqlalchemy import update
    stmt = update(Lead).where(Lead.campaign_id == None).values(campaign_id=campaign_id)
    result = await db.execute(stmt)
    await db.commit()
    return {"status": "success", "updated_count": result.rowcount}

@router.post("/tools/restore")
async def restore_leads(
    leads_data: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.email != "admin@revo.ai":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from app.models.contact import Contact
    
    for item in leads_data:
        lead = Lead(
            company_name=item.get("company_name", "Unknown"),
            business_type=item.get("business_type"),
            city="Dubai",
            address=item.get("address"),
            website=item.get("website"),
            rating=float(item.get("rating") or item.get("totalScore") or 0.0),
            reviews_count=int(item.get("reviews_count") or item.get("reviewsCount") or item.get("reviews") or 0),
            custom_data={}
        )
        db.add(lead)
        await db.flush() # flush to get lead.id
        
        if item.get("phone"):
            db.add(Contact(lead_id=lead.id, contact_type="phone", contact_value=str(item["phone"])[:50]))
        if item.get("email"):
            db.add(Contact(lead_id=lead.id, contact_type="email", contact_value=str(item["email"])[:50]))
            
    await db.commit()
    return {"status": "success", "restored": len(leads_data)}

@router.post("/tools/reset_enrichment")
async def reset_enrichment_status(payload: dict, db: AsyncSession = Depends(get_db)):
    """Reset stuck in_progress status for selected leads."""
    from sqlalchemy import cast, String
    lead_ids = payload.get("lead_ids", [])
    select_all = payload.get("select_all", False)
    filters = payload.get("filters", {})

    query = select(Lead)
    if select_all:
        query = apply_lead_filters(query, filters)
    else:
        if not lead_ids:
            return {"status": "ok", "reset_count": 0}
        query = query.where(cast(Lead.id, String).in_(lead_ids))

    res = await db.execute(query)
    leads = res.scalars().all()
    count = 0
    for l in leads:
        if l.custom_data and l.custom_data.get("enrichment_status") == "in_progress":
            existing = dict(l.custom_data)
            existing.pop("enrichment_status", None)
            if "ai_logs" not in existing:
                existing["ai_logs"] = []
            existing["ai_logs"].append("[WARNING] Enrichment was manually cancelled or reset by user.")
            l.custom_data = existing
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(l, "custom_data")
            count += 1
            
    await db.commit()
    return {"status": "ok", "reset_count": count}

@router.post("/tools/enrich")
async def trigger_targeted_enrichment(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead_ids = body.get("lead_ids", [])
    select_all = body.get("select_all", False)
    
    from sqlalchemy import cast, String
    if select_all:
        filters = body.get("filters", {})
        stmt = apply_lead_filters(select(Lead.id), filters)
        # Apply the same default sorting as the UI
        stmt = stmt.order_by(Lead.created_at.desc())
        res = await db.execute(stmt)
        lead_ids = [str(i) for i in res.scalars().all()]
        
    if not lead_ids:
        raise HTTPException(status_code=400, detail="No leads found or provided")
        
    # Set status to in_progress immediately
    from sqlalchemy import cast, String
    from sqlalchemy.orm.attributes import flag_modified
    leads_res = await db.execute(select(Lead).where(cast(Lead.id, String).in_(lead_ids)))
    leads = leads_res.scalars().all()
    for l in leads:
        existing = dict(l.custom_data) if l.custom_data else {}
        existing["enrichment_status"] = "in_progress"
        l.custom_data = existing
        flag_modified(l, "custom_data")
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

class ActionRequest(BaseModel):
    lead_ids: Optional[List[UUID]] = None
    select_all: Optional[bool] = False
    filters: Optional[dict] = None

@router.post("/check_messengers")
async def check_messengers(
    body: ActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select, cast, String
    from sqlalchemy.orm.attributes import flag_modified
    from app.services.messenger_checker import verify_messenger_availability

    if body.select_all:
        stmt = apply_lead_filters(select(Lead), body.filters or {})
    else:
        stmt = select(Lead).where(cast(Lead.id, String).in_([str(id) for id in (body.lead_ids or [])]))
        
    res = await db.execute(stmt)
    leads = res.scalars().all()

    count = 0
    for lead in leads:
        if lead.phone:
            info = verify_messenger_availability(lead.phone)
            existing = dict(lead.custom_data) if lead.custom_data else {}
            existing["telegram_available"] = info.get("telegram_available", False)
            existing["whatsapp_available"] = info.get("whatsapp_available", False)
            existing["viber_available"] = info.get("viber_available", False)
            lead.custom_data = existing
            flag_modified(lead, "custom_data")
            count += 1

    await db.commit()
    return {"message": f"Checked messengers for {count} leads"}

@router.post("/export_lead_radar")
async def export_lead_radar(
    body: ActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select, cast, String
    from fastapi.responses import JSONResponse
    
    if body.select_all:
        stmt = apply_lead_filters(select(Lead), body.filters or {})
    else:
        stmt = select(Lead).where(cast(Lead.id, String).in_([str(id) for id in (body.lead_ids or [])]))
        
    res = await db.execute(stmt)
    leads = res.scalars().all()

    export_data = []
    for lead in leads:
        cd = lead.custom_data or {}
        platform = None
        if cd.get("telegram_available"):
            platform = "telegram"
        elif cd.get("whatsapp_available"):
            platform = "whatsapp"
        
        if platform:
            export_data.append({
                "telegram_id": lead.phone,
                "author_username": lead.phone,
                "niche_code": lead.business_type,
                "chat_title": lead.company_name,
                "raw_ad_text": lead.description or "",
                "sales_hook": cd.get("draft_email", ""),
                "confidence_score": lead.revo_score,
                "platform": platform
            })

    return JSONResponse(content={"status": "success", "exported": len(export_data), "data": export_data})
