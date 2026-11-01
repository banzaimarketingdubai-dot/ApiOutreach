import uuid
import csv
import io
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.audience import Audience
from app.models.project import Project
from app.models.lead import Lead
from app.models.contact import Contact
from app.schemas.audience import AudienceCreate, AudienceUpdate, AudienceResponse

router = APIRouter()

async def compute_audience_stats(db: AsyncSession, audience_id: uuid.UUID) -> dict:
    total_leads = (await db.execute(select(func.count(Lead.id)).where(Lead.audience_id == audience_id))).scalar() or 0
    
    # Leads with email contacts
    email_leads_stmt = (
        select(func.count(func.distinct(Lead.id)))
        .join(Contact, Contact.lead_id == Lead.id)
        .where(Lead.audience_id == audience_id, func.lower(Contact.contact_type) == "email")
    )
    with_email = (await db.execute(email_leads_stmt)).scalar() or 0
    
    # Leads with phone contacts
    phone_leads_stmt = (
        select(func.count(func.distinct(Lead.id)))
        .join(Contact, Contact.lead_id == Lead.id)
        .where(Lead.audience_id == audience_id, func.lower(Contact.contact_type) == "phone")
    )
    with_phone = (await db.execute(phone_leads_stmt)).scalar() or 0
    
    # Enriched (has custom_data with attributes)
    enriched_stmt = (
        select(func.count(Lead.id))
        .where(Lead.audience_id == audience_id, Lead.custom_data.isnot(None), Lead.custom_data != {})
    )
    enriched = (await db.execute(enriched_stmt)).scalar() or 0
    
    return {
        "total_leads": total_leads,
        "with_email": with_email,
        "with_phone": with_phone,
        "enriched": enriched
    }

def map_row_to_lead_dict(raw_dict: dict) -> Optional[dict]:
    normalized = {}
    custom_data = {}
    
    mapping_rules = {
        "company_name": ["company_name", "company", "name", "title", "организация", "название", "бизнес", "заведение"],
        "business_type": ["business_type", "type", "category", "niche", "категория", "ниша", "тип"],
        "city": ["city", "town", "location", "город", "населенный пункт"],
        "address": ["address", "street", "адрес", "улица"],
        "website": ["website", "site", "url", "web", "сайт"],
        "email": ["email", "e-mail", "mail", "почта", "электронная почта"],
        "phone": ["phone", "tel", "telephone", "mobile", "телефон", "номер", "тел"],
        "rating": ["rating", "stars", "рейтинг", "оценка"]
    }
    
    for k, v in raw_dict.items():
        if v is None:
            continue
        str_val = str(v).strip()
        if not str_val:
            continue
            
        clean_key = str(k).strip().lower().replace(" ", "_").replace("-", "_")
        matched_field = None
        for target_field, synonyms in mapping_rules.items():
            if clean_key in synonyms or any(syn in clean_key for syn in synonyms):
                matched_field = target_field
                break
                
        if matched_field:
            if matched_field == "rating":
                try:
                    normalized[matched_field] = float(str_val.replace(",", "."))
                except Exception:
                    pass
            else:
                normalized[matched_field] = str_val
        else:
            custom_data[str(k).strip()] = str_val
            
    if not normalized.get("company_name"):
        return None
        
    return {
        "company_name": normalized.get("company_name"),
        "business_type": normalized.get("business_type"),
        "city": normalized.get("city"),
        "address": normalized.get("address"),
        "website": normalized.get("website"),
        "email": normalized.get("email"),
        "phone": normalized.get("phone"),
        "rating": normalized.get("rating", 0.0),
        "custom_data": custom_data
    }

@router.get("", response_model=List[AudienceResponse])
async def list_audiences(
    project_id: Optional[uuid.UUID] = Query(None, description="Filter audiences by project ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List audiences with live lead count and stats."""
    stmt = select(Audience)
    if project_id:
        stmt = stmt.where(Audience.project_id == project_id)
    stmt = stmt.order_by(Audience.created_at.desc())
    
    res = await db.execute(stmt)
    audiences = res.scalars().all()
    
    result = []
    for aud in audiences:
        leads_count = (await db.execute(select(func.count(Lead.id)).where(Lead.audience_id == aud.id))).scalar() or 0
        resp = AudienceResponse.model_validate(aud)
        resp.leads_count = leads_count
        result.append(resp)
        
    return result

@router.post("", response_model=AudienceResponse, status_code=status.HTTP_201_CREATED)
async def create_audience(
    data: AudienceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new contact audience list."""
    proj = (await db.execute(select(Project).where(Project.id == data.project_id))).scalars().first()
    if not proj:
        raise HTTPException(status_code=400, detail="Target project not found")

    new_aud = Audience(
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        source_type=data.source_type or "PARSER",
        stats={"total_leads": 0, "with_email": 0, "with_phone": 0, "enriched": 0},
        custom_fields_schema=data.custom_fields_schema or []
    )
    db.add(new_aud)
    await db.commit()
    await db.refresh(new_aud)
    
    resp = AudienceResponse.model_validate(new_aud)
    resp.leads_count = 0
    return resp

@router.get("/{audience_id}", response_model=AudienceResponse)
async def get_audience(
    audience_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audience details and refreshed stats."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    stats = await compute_audience_stats(db, aud.id)
    aud.stats = stats
    await db.commit()
    await db.refresh(aud)

    resp = AudienceResponse.model_validate(aud)
    resp.leads_count = stats["total_leads"]
    return resp

@router.put("/{audience_id}", response_model=AudienceResponse)
async def update_audience(
    audience_id: uuid.UUID,
    data: AudienceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update audience metadata."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    if data.name is not None:
        aud.name = data.name
    if data.description is not None:
        aud.description = data.description
    if data.source_type is not None:
        aud.source_type = data.source_type
    if data.custom_fields_schema is not None:
        aud.custom_fields_schema = data.custom_fields_schema

    await db.commit()
    await db.refresh(aud)

    leads_count = (await db.execute(select(func.count(Lead.id)).where(Lead.audience_id == aud.id))).scalar() or 0
    resp = AudienceResponse.model_validate(aud)
    resp.leads_count = leads_count
    return resp

@router.delete("/{audience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audience(
    audience_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an audience and its leads."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    await db.delete(aud)
    await db.commit()
    return None

@router.post("/{audience_id}/import-rows")
async def import_rows_to_audience(
    audience_id: uuid.UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import an array of lead dicts into this audience with deduplication."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    rows = payload.get("rows", [])
    if not rows:
        raise HTTPException(status_code=400, detail="No rows provided in payload")

    imported_count = 0
    duplicate_count = 0

    for raw in rows:
        lead_dict = map_row_to_lead_dict(raw)
        if not lead_dict:
            continue
            
        dup_conditions = [Lead.audience_id == aud.id, Lead.company_name.ilike(lead_dict["company_name"])]
        if lead_dict.get("city"):
            dup_conditions.append(Lead.city.ilike(lead_dict["city"]))
        if lead_dict.get("website"):
            dup_check = or_(and_(*dup_conditions), and_(Lead.audience_id == aud.id, Lead.website == lead_dict["website"]))
        else:
            dup_check = and_(*dup_conditions)

        existing = (await db.execute(select(Lead.id).where(dup_check))).scalar()
        if existing:
            duplicate_count += 1
            continue

        email = lead_dict.pop("email", None)
        phone = lead_dict.pop("phone", None)

        new_lead = Lead(
            project_id=aud.project_id,
            audience_id=aud.id,
            **lead_dict
        )
        db.add(new_lead)
        await db.flush()

        if email:
            db.add(Contact(
                lead_id=new_lead.id,
                contact_type="email",
                contact_value=email,
                source="import",
                is_primary=True
            ))
        if phone:
            db.add(Contact(
                lead_id=new_lead.id,
                contact_type="phone",
                contact_value=phone,
                source="import",
                is_primary=True
            ))

        imported_count += 1

    await db.commit()
    stats = await compute_audience_stats(db, aud.id)
    aud.stats = stats
    await db.commit()

    return {
        "status": "success",
        "imported": imported_count,
        "duplicates_skipped": duplicate_count,
        "stats": stats
    }

@router.post("/{audience_id}/import-file")
async def import_file_to_audience(
    audience_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import CSV or XLSX file directly into this audience."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    content = await file.read()
    filename = (file.filename or "").lower()
    rows = []

    try:
        if filename.endswith(".csv") or filename.endswith(".txt"):
            text_stream = io.StringIO(content.decode("utf-8", errors="ignore"))
            reader = csv.DictReader(text_stream)
            rows = [dict(row) for row in reader]
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            import pandas as pd
            df = pd.read_excel(io.BytesIO(content))
            rows = df.to_dict(orient="records")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .csv or .xlsx")
    except Exception as parse_err:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(parse_err)}")

    if not rows:
        raise HTTPException(status_code=400, detail="File is empty or contains no valid rows")

    return await import_rows_to_audience(audience_id, {"rows": rows}, db, current_user)

@router.post("/{audience_id}/enrich")
async def trigger_audience_enrichment(
    audience_id: uuid.UUID,
    body: Optional[dict] = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger background AI enrichment for all unenriched leads in this audience."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    only_unenriched = body.get("only_unenriched", True) if body else True
    lead_query = select(Lead).where(Lead.audience_id == audience_id, Lead.website.isnot(None), Lead.website != "")
    if only_unenriched:
        lead_query = lead_query.where(
            or_(
                Lead.custom_data.is_(None),
                Lead.custom_data['enrichment_status'].astext.is_(None),
                Lead.custom_data['enrichment_status'].astext != "completed"
            )
        )
    leads = (await db.execute(lead_query)).scalars().all()
    if not leads:
        return {"status": "ok", "message": "No eligible leads with website found to enrich in this audience", "queued": 0}

    lead_ids = [str(l.id) for l in leads]
    
    from sqlalchemy.orm.attributes import flag_modified
    for l in leads:
        existing = dict(l.custom_data) if l.custom_data else {}
        existing["enrichment_status"] = "in_progress"
        l.custom_data = existing
        flag_modified(l, "custom_data")
    await db.commit()

    from app.workers.enrichment_tasks import run_targeted_enrichment
    run_targeted_enrichment.delay(lead_ids, None)

    return {"status": "success", "message": f"Enrichment queued for {len(lead_ids)} leads", "queued": len(lead_ids)}

@router.post("/{audience_id}/recalculate-stats", response_model=AudienceResponse)
async def recalculate_audience_stats(
    audience_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Explicitly re-compute and persist aggregate stats for an audience."""
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    stats = await compute_audience_stats(db, aud.id)
    aud.stats = stats
    await db.commit()
    await db.refresh(aud)

    resp = AudienceResponse.model_validate(aud)
    resp.leads_count = stats["total_leads"]
    return resp

class AttachLeadsRequest(BaseModel):
    lead_ids: Optional[List[uuid.UUID]] = None
    city: Optional[str] = None
    min_rating: Optional[float] = None
    has_email: Optional[bool] = False
    has_phone: Optional[bool] = False
    limit: Optional[int] = 100

@router.post("/{audience_id}/attach-leads")
async def attach_leads_to_audience(
    audience_id: uuid.UUID,
    body: AttachLeadsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Audience).where(Audience.id == audience_id)
    aud = (await db.execute(stmt)).scalars().first()
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    from app.models.contact import Contact, ChannelType
    
    if body.lead_ids:
        lead_stmt = select(Lead).where(Lead.id.in_(body.lead_ids))
    else:
        lead_stmt = select(Lead)
        if body.city:
            lead_stmt = lead_stmt.where(Lead.city.ilike(f"%{body.city}%"))
        if body.min_rating:
            lead_stmt = lead_stmt.where(Lead.rating >= body.min_rating)
        if body.has_email:
            lead_stmt = lead_stmt.join(Contact, Lead.id == Contact.lead_id).where(Contact.channel == ChannelType.EMAIL, Contact.is_valid == True)
        if body.has_phone:
            lead_stmt = lead_stmt.join(Contact, Lead.id == Contact.lead_id).where(Contact.channel.in_([ChannelType.PHONE, ChannelType.WHATSAPP]), Contact.is_valid == True)
        lead_stmt = lead_stmt.limit(body.limit or 100)

    res = await db.execute(lead_stmt)
    leads_to_attach = res.scalars().unique().all()

    attached_count = 0
    for l in leads_to_attach:
        l.audience_id = aud.id
        l.project_id = aud.project_id
        attached_count += 1

    await db.commit()
    stats = await compute_audience_stats(db, aud.id)
    aud.stats = stats
    await db.commit()

    return {
        "status": "success",
        "attached_count": attached_count,
        "audience_id": str(aud.id),
        "total_leads": stats.get("total_leads", 0)
    }

class ExportGoogleSheetsRequest(BaseModel):
    spreadsheet_id: Optional[str] = None
    custom_template: Optional[Dict[str, Any]] = None

@router.post("/{audience_id}/export-google-sheets")
async def export_audience_google_sheets(
    audience_id: uuid.UUID,
    body: Optional[ExportGoogleSheetsRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exports all leads from the specified Audience into a dedicated Google Sheet tab.
    Saves the spreadsheet live URL to audience stats.
    """
    stmt = select(Audience).where(Audience.id == audience_id)
    audience = (await db.execute(stmt)).scalars().first()
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")

    # Fetch all leads in this audience with eager-loaded contacts
    leads_stmt = select(Lead).where(Lead.audience_id == audience_id).order_by(Lead.created_at.desc())
    res = await db.execute(leads_stmt)
    leads = res.scalars().unique().all()

    if not leads:
        raise HTTPException(
            status_code=400,
            detail="В этой аудитории пока нет лидов для экспорта. Добавьте контакты через парсер или сегментацию базы."
        )

    from app.services.google_sheets_service import export_audience_leads_to_google_sheet

    try:
        spreadsheet_id = body.spreadsheet_id if body else None
        custom_template = body.custom_template if body else None
        
        result = export_audience_leads_to_google_sheet(
            audience_name=audience.name,
            leads=leads,
            spreadsheet_id=spreadsheet_id,
            template_config=custom_template
        )

        # Update audience stats with google sheet url
        current_stats = dict(audience.stats or {})
        current_stats["google_sheet_url"] = result["sheet_url"]
        current_stats["google_sheet_exported_at"] = result["exported_at"]
        current_stats["google_sheet_leads_count"] = result["leads_exported"]
        current_stats["google_sheet_title"] = result["sheet_title"]
        audience.stats = current_stats

        await db.commit()
        await db.refresh(audience)

        return result
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        logger.error(f"Google Sheets export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта в Google Sheets: {str(e)}")

