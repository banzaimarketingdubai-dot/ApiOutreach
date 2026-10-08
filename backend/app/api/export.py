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
