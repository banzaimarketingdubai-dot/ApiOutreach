import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.lead import Lead

router = APIRouter()

@router.get("/csv")
async def export_leads_csv(
    min_score: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Lead).order_by(desc(Lead.created_at))
    if min_score is not None:
        stmt = stmt.where(Lead.revo_score >= min_score)
    if city:
        stmt = stmt.where(Lead.city.ilike(f"%{city}%"))

    res = await db.execute(stmt)
    leads = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Lead ID", "Company Name", "Business Type", "City", "Address",
        "Website", "Rating", "Reviews Count", "Revo Score", "Phones", "Emails",
        "WhatsApp", "Custom Data (JSON)"
    ])

    for l in leads:
        phones = [c.contact_value for c in l.contacts if c.contact_type == "phone"]
        emails = [c.contact_value for c in l.contacts if c.contact_type == "email"]
        whatsapp = [c.contact_value for c in l.contacts if c.contact_type == "whatsapp"]

        writer.writerow([
            str(l.id),
            l.company_name,
            l.business_type or "",
            l.city or "",
            l.address or "",
            l.website or "",
            l.rating,
            l.reviews_count,
            l.revo_score,
            ", ".join(phones),
            ", ".join(emails),
            ", ".join(whatsapp),
            str(l.custom_data or {})
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=revo_master_data_leads.csv"}
    )

from pydantic import BaseModel
from typing import List

class HubspotExportRequest(BaseModel):
    lead_ids: List[str]

@router.post("/hubspot")
async def export_leads_hubspot(
    body: HubspotExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.vault_helper import get_api_key
    import httpx
    
    hubspot_key = await get_api_key("hubspot")
    if not hubspot_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="HubSpot API Key is not configured in the Vault.")
        
    import uuid
    stmt = select(Lead).where(Lead.id.in_([uuid.UUID(i) for i in body.lead_ids]))
    res = await db.execute(stmt)
    leads = res.scalars().all()
    
    if not leads:
        return {"status": "success", "exported_count": 0}

    url = "https://api.hubapi.com/crm/v3/objects/companies/batch/create"
    headers = {
        "Authorization": f"Bearer {hubspot_key}",
        "Content-Type": "application/json"
    }
    
    inputs = []
    for l in leads:
        props = {
            "name": l.company_name,
            "domain": l.website or "",
            "city": l.city or "",
            "address": l.address or "",
            "phone": l.phone or "",
            "description": f"Revo Score: {l.revo_score}\nAudit Notes: {l.audit_notes or ''}"
        }
        inputs.append({"properties": props})
        
    payload = {"inputs": inputs}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        
        # If unauthorized, bubble it up
        if resp.status_code == 401:
            raise HTTPException(status_code=401, detail="HubSpot API Key is invalid or expired.")
            
        # For other errors, we might still want to see what happened
        if resp.status_code not in [200, 201, 207]:
            raise HTTPException(status_code=500, detail=f"HubSpot API error: {resp.text}")
            
    return {"status": "success", "exported_count": len(leads)}

from datetime import datetime

class WebhookExportRequest(BaseModel):
    lead_ids: List[str]
    webhook_url: str

@router.post("/webhook")
async def export_leads_webhook(
    body: WebhookExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import httpx, uuid
    stmt = select(Lead).where(Lead.id.in_([uuid.UUID(i) for i in body.lead_ids]))
    res = await db.execute(stmt)
    leads = res.scalars().all()
    
    if not leads:
        return {"status": "success", "exported_count": 0}

    payload = {
        "event": "leads.sync",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "leads": []
    }
    
    for l in leads:
        contacts_data = [{"type": c.contact_type, "value": c.contact_value} for c in l.contacts]
        payload["leads"].append({
            "lead_id": str(l.id),
            "company_name": l.company_name,
            "business_type": l.business_type,
            "city": l.city,
            "address": l.address,
            "website": l.website,
            "rating": l.rating,
            "reviews_count": l.reviews_count,
            "revo_score": l.revo_score,
            "audit_notes": l.audit_notes,
            "contacts": contacts_data
        })
        
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(body.webhook_url, json=payload)
            if resp.status_code >= 400:
                from fastapi import HTTPException
                raise HTTPException(status_code=500, detail=f"Webhook failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to trigger webhook: {str(e)}")
        
    return {"status": "success", "exported_count": len(leads)}
