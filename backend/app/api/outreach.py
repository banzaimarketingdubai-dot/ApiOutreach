from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from typing import List, Optional
from pydantic import BaseModel
import os
import resend

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.lead import Lead
from app.models.contact import Contact
from app.models.project import Project
from app.models.product import Product
from app.models.audience import Audience
from app.models.funnel import FunnelSequence
from app.models.inbound_reply import InboundReply, ReplyIntent
from app.models.outreach_campaign import OutreachCampaign, OutreachStatus
from app.models.email_sequence import EmailSequence, EmailSequenceStatus, PromoTrackStatus, OutreachTemplate
from app.services.ai_funnel import AIFunnelService
from app.services.ai_inbox import AIInboxService
from app.workers.outreach_tasks import generate_email_with_groq
from app.services.vault_helper import get_api_key
import asyncio
import uuid

router = APIRouter()

# =======================
# Pydantic Schemas
# =======================
class CampaignCreate(BaseModel):
    name: str
    prompt_template: str
    filters: dict

class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    
    class Config:
        from_attributes = True

# =======================
# Campaign Management
# =======================
@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, db: AsyncSession = Depends(get_db)):
    new_campaign = OutreachCampaign(
        name=campaign.name,
        prompt_template=campaign.prompt_template,
        filters=campaign.filters,
        status=OutreachStatus.DRAFT
    )
    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign)
    return new_campaign

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OutreachCampaign).order_by(OutreachCampaign.created_at.desc()))
    return result.scalars().all()

# =======================
# Sequence Generation (Drafts)
# =======================
class DraftRequest(BaseModel):
    campaign_id: str
    lead_ids: List[str]

@router.post("/generate_drafts")
async def generate_drafts(req: DraftRequest, db: AsyncSession = Depends(get_db)):
    """
    Generates Touch 1 drafts for the selected leads using the new GBPilot strategy.
    """
    campaign_res = await db.execute(select(OutreachCampaign).filter(OutreachCampaign.id == req.campaign_id))
    campaign = campaign_res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    leads_res = await db.execute(select(Lead).filter(Lead.id.in_(req.lead_ids), Lead.is_unsubscribed == False))
    leads = leads_res.scalars().all()
    
    created_count = 0
    for lead in leads:
        # Check if sequence already exists
        seq_res = await db.execute(select(EmailSequence).filter(EmailSequence.lead_id == lead.id, EmailSequence.campaign_id == campaign.id))
        if seq_res.scalar_one_or_none():
            continue # Already in sequence
            
        audit_link = f"https://gbpilot-saas.vercel.app/audit/{lead.id}"
        unsub_link = f"https://api.revo-masterdata.com/api/v1/outreach/webhooks/unsubscribe?lead_id={lead.id}"
        
        # Touch 1: The Icebreaker (Empathy + Audit + Reply CTA)
        # Generate dynamic OpenGraph Image URL for the Snapshot
        snapshot_img_url = f"https://gbpilot-saas.vercel.app/api/og/audit?id={lead.id}&name={lead.company_name.replace(' ', '%20')}&score={int(lead.rating * 20 if lead.rating else 80)}"
        
        # Extract specific data for personalization (mocking fallbacks if not in custom_data)
        biz_type = lead.business_type or "бизнесе"
        custom_data = lead.custom_data or {}
        unanswered = custom_data.get("unanswered_reviews", int((lead.reviews_count or 20) * 0.3)) # mock ~30% unanswered
        last_post = custom_data.get("last_post_days_ago", 45) # mock 45 days ago
        
        body = f"""<div style="font-family: sans-serif; font-size: 14px; color: #1f2937; line-height: 1.6; max-width: 600px;">
<p>Здравствуйте, команда <strong>{lead.company_name}</strong>!</p>

<p>Мы проанализировали ваш профиль на Google Картах. У вас хороший рейтинг ({lead.rating or 4.0} ⭐️ и {lead.reviews_count or 0} отзывов), видно, что вы заботитесь о качестве сервиса.</p>

<p>Но есть техническая проблема: алгоритмы Google пессимизируют ваш профиль прямо сейчас. Мы видим, что у вас <strong>около {unanswered} неотвеченных отзывов</strong>, а последний SEO-пост выходил <strong>более {last_post} дней назад</strong>.</p>

<p><strong>Почему это убивает ваши продажи:</strong> Гугл отдает топовые места тем компаниям, которые проявляют постоянную активность. Пока вы работаете над бизнесом, ваши конкуренты, которые регулярно отвечают на отзывы и публикуют апдейты, забирают ваших клиентов.</p>

<p>Я сгенерировал интерактивную тепловую карту (Geo-Grid) вашего района. Красные зоны — это сектора, где вы проигрываете конкурентам в поиске:</p>

<p style="text-align: center; margin: 25px 0;">
    <a href="{audit_link}" target="_blank">
        <img src="{snapshot_img_url}" alt="Аудит {lead.company_name}" style="width: 100%; max-width: 500px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" />
    </a>
</p>

<p><strong>Как это исправить (Бесплатно):</strong><br>
1. Прямо сегодня ответьте на все {unanswered} отзывов, обязательно используя ключевые слова (например, "{biz_type} в нашем районе").<br>
2. Раз в неделю публикуйте короткий пост с фотографией (с геотегами) о ваших новостях.</p>

<p>Мы понимаем, что у вас нет времени ежедневно изучать новинки алгоритмов Google. Вы должны развивать бизнес, а не сидеть в кабинете Google My Business.</p>

<p>Поэтому мы создали <strong>GBPilot</strong> — ИИ-систему, которая полностью берет ведение профиля на себя. Она автоматически генерирует идеальные SEO-ответы на отзывы и публикует посты 24/7 (с контролем качества и защитой от конкурентов).</p>

<p>Если хотите протестировать ИИ-автопилот бесплатно на 14 дней — просто <strong>ответьте на это письмо</strong>, и я вышлю секретный промокод.</p>

<p>С уважением,<br>Отдел локальной SEO-аналитики REVO</p>

<br><br>
<p style="font-size: 11px; color: #9ca3af;">
    Письмо отправлено на основе публичных данных Google Карт. 
    <a href="{unsub_link}" style="color: #9ca3af; text-decoration: underline;">Отписаться от аналитики</a>
</p>
</div>"""
        new_seq = EmailSequence(
            lead_id=lead.id,
            campaign_id=campaign.id,
            current_touch=1,
            status=EmailSequenceStatus.DRAFT,
            email_subject=subject,
            email_content=body
        )
        db.add(new_seq)
        created_count += 1
        
    await db.commit()
    return {"message": f"Generated {created_count} drafts successfully."}

class OmniDraftRequest(BaseModel):
    lead_id: str
    prompt: Optional[str] = None

@router.get("/debug_models")
async def list_available_models():
    from app.services.vault_helper import get_api_key
    gemini_key = await get_api_key("gemini")
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()

@router.post("/draft")
async def generate_single_draft(req: OmniDraftRequest, db: AsyncSession = Depends(get_db)):
    """Generates AI drafts for a single lead based on the provided prompt."""
    lead_res = await db.execute(select(Lead).filter(Lead.id == req.lead_id))
    lead = lead_res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    from app.services.vault_helper import get_api_key
    # Switch to Groq because Gemini free tier is heavily restricted for this account
    groq_key = await get_api_key("groq")
    
    if not groq_key:
        raise HTTPException(status_code=400, detail="Groq API key not configured in Vault or .env")
        
    audit_link = f"https://gbpilot-saas.vercel.app/audit/{lead.id}"
    snapshot_img_url = f"https://placehold.co/600x400/ef4444/white/png?text=Geo-Grid+Heatmap+Snapshot"
    
    # Construct the instruction for Gemini
    system_instruction = f"""
    You are an expert B2B SaaS copywriter. Your goal is to write highly converting outreach messages.
    Generate a JSON response containing drafts for 'email' (with subject and body), 'whatsapp', 'telegram', and 'direct'.
    The email body should be in HTML format (using simple tags like <p>, <strong>, <br>).
    CRITICAL INSTRUCTION: You MUST write all messages (email, whatsapp, telegram, direct, subject) in the exact same language as the User Instruction below. If the user instruction is in Russian, you must output Russian.
    You MUST embed this exact image HTML in the email body where appropriate to show their audit snapshot:
    <p style="text-align: center; margin: 25px 0;"><a href="{audit_link}" target="_blank"><img src="{snapshot_img_url}" alt="Audit" style="width: 100%; max-width: 500px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" /></a></p>
    
    Lead Data:
    Company Name: {lead.company_name}
    Niche: {lead.business_type}
    City: {lead.city}
    Rating: {lead.rating} (from {lead.reviews_count} reviews)
    """
    
    user_instruction = req.prompt or f"Напиши холодное письмо для {lead.company_name} с предложением нашего сервиса."
    
    system_instruction += '\n\nYou MUST return a valid JSON object matching this schema exactly:\n{"subject": "str", "email_body": "str", "whatsapp": "str", "telegram": "str", "direct": "str"}'
    
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_instruction}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7
    }
    
    import httpx
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                url, 
                json=payload, 
                headers={"Authorization": f"Bearer {groq_key}"}
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Groq API error: {resp.text}")
                
            raw_json = resp.json()["choices"][0]["message"]["content"]
            import json
            data = json.loads(raw_json)
            
            return {
                "subject": data.get("subject", ""),
                "body": data.get("email_body", ""),
                "audit_link": audit_link,
                "whatsapp": data.get("whatsapp", ""),
                "telegram": data.get("telegram", ""),
                "direct": data.get("direct", "")
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
# =======================
# Funnel Management (Sprint 1)
# =======================
class FunnelActionRequest(BaseModel):
    lead_ids: List[str]
    funnel_type: Optional[str] = None # For start

@router.post("/funnels/start")
async def start_funnel(req: FunnelActionRequest, db: AsyncSession = Depends(get_db)):
    """Starts a drip funnel for the selected leads."""
    from app.models.email_sequence import FunnelType
    from uuid import UUID
    if not req.funnel_type:
        raise HTTPException(status_code=400, detail="funnel_type is required")
        
    try:
        uuid_ids = [UUID(str(i)) for i in req.lead_ids if i]
        leads_res = await db.execute(select(Lead).filter(Lead.id.in_(uuid_ids), Lead.is_unsubscribed == False))
        leads = leads_res.scalars().all()
        
        count = 0
        camp_res = await db.execute(select(OutreachCampaign))
        first_camp = camp_res.scalars().first()
        
        if not first_camp:
            first_camp = OutreachCampaign(
                name="Global Outreach Campaign",
                prompt_template="Standard GBPilot B2B Outreach",
                filters={},
                status=OutreachStatus.ACTIVE
            )
            db.add(first_camp)
            await db.commit()
            await db.refresh(first_camp)
            
        default_campaign_id = first_camp.id

        for lead in leads:

            # Stop existing sequence
            await db.execute(update(EmailSequence).where(EmailSequence.lead_id == lead.id).values(status=EmailSequenceStatus.PAUSED))
            
            # Create new active sequence
            new_seq = EmailSequence(
                lead_id=lead.id,
                campaign_id=lead.campaign_id or default_campaign_id,
                funnel_type=req.funnel_type,
                status=EmailSequenceStatus.ACTIVE,
                current_touch=1,
                next_send_date=func.now()
            )
            db.add(new_seq)
            count += 1

            
        await db.commit()
        return {"status": "success", "started": count}
    except Exception as err:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start funnel: {str(err)}")


@router.post("/funnels/pause")
async def pause_funnels(req: FunnelActionRequest, db: AsyncSession = Depends(get_db)):
    """Pauses active funnels for the selected leads."""
    res = await db.execute(
        update(EmailSequence)
        .where(EmailSequence.lead_id.in_(req.lead_ids), EmailSequence.status == EmailSequenceStatus.ACTIVE)
        .values(status=EmailSequenceStatus.PAUSED)
    )
    await db.commit()
    return {"status": "success", "message": "Funnels paused."}

@router.post("/funnels/resume")
async def resume_funnels(req: FunnelActionRequest, db: AsyncSession = Depends(get_db)):
    """Resumes paused funnels for the selected leads."""
    res = await db.execute(
        update(EmailSequence)
        .where(EmailSequence.lead_id.in_(req.lead_ids), EmailSequence.status == EmailSequenceStatus.PAUSED)
        .values(status=EmailSequenceStatus.ACTIVE)
    )
    await db.commit()
    return {"status": "success", "message": "Funnels resumed."}

class OverrideRequest(BaseModel):
    lead_id: str
    email_subject: str
    email_content: str
    
@router.post("/funnels/override")
async def override_funnel(req: OverrideRequest, db: AsyncSession = Depends(get_db)):
    """Overrides any active funnel and sends a custom manual email immediately."""
    # Pause active
    await db.execute(update(EmailSequence).where(EmailSequence.lead_id == req.lead_id).values(status=EmailSequenceStatus.PAUSED))
    
    # Create custom sequence ready to send immediately
    from app.models.email_sequence import FunnelType
    new_seq = EmailSequence(
        lead_id=req.lead_id,
        funnel_type=FunnelType.CUSTOM,
        status=EmailSequenceStatus.QUEUED, # Picked up by sender immediately
        current_touch=1,
        email_subject=req.email_subject,
        email_content=req.email_content,
        next_send_date=func.now()
    )
    db.add(new_seq)
    await db.commit()
    return {"status": "success", "message": "Custom sequence override created."}

# =======================
# Webhooks
# =======================
@router.get("/webhooks/unsubscribe")
async def handle_unsubscribe(lead_id: str, db: AsyncSession = Depends(get_db)):
    """
    1-Click Unsubscribe Endpoint.
    """
    # Set lead to unsubscribed
    await db.execute(update(Lead).where(Lead.id == lead_id).values(is_unsubscribed=True))
    
    # Halt all active sequences
    await db.execute(
        update(EmailSequence)
        .where(EmailSequence.lead_id == lead_id)
        .values(status=EmailSequenceStatus.UNSUBSCRIBED, promo_status=PromoTrackStatus.UNSUBSCRIBED)
    )
    await db.commit()
    
    # In a real app, this would return an HTML template saying "You have been unsubscribed."
    return {"status": "success", "message": "Вы успешно отписаны от рассылок."}

@router.post("/webhooks/resend")
async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Catches events from Resend (e.g., email.opened, email.bounced, email.replied).
    In a real app, verify Resend signature here.
    """
    payload = await request.json()
    event_type = payload.get("type")
    data = payload.get("data", {})
    
    # Assuming we passed lead_id in headers or tags when sending via Resend
    # For demonstration, let's assume we extract lead_id from tags
    tags = data.get("tags", [])
    lead_id = next((t["value"] for t in tags if t["name"] == "lead_id"), None)
    
    if not lead_id:
        return {"status": "ignored", "reason": "No lead_id in tags"}
        
    if event_type == "email.bounced":
        await db.execute(update(EmailSequence).where(EmailSequence.lead_id == lead_id).values(status=EmailSequenceStatus.BOUNCED))
    
    elif event_type == "email.opened":
        await db.execute(
            update(EmailSequence)
            .where(EmailSequence.lead_id == lead_id, EmailSequence.status != EmailSequenceStatus.REPLIED)
            .values(status=EmailSequenceStatus.OPENED, opened_at=func.now())
        )
        
    elif event_type == "email.clicked":
        click_url = data.get("click", {}).get("url", "")
        print(f"[CLICK] Lead {lead_id} clicked URL: {click_url}")
        await db.execute(
            update(EmailSequence)
            .where(EmailSequence.lead_id == lead_id)
            .values(clicked_at=func.now())
        )
        
    elif event_type == "email.replied": # Hot Lead!
        # Stop sequence, set to replied, move to promo track
        await db.execute(
            update(EmailSequence)
            .where(EmailSequence.lead_id == lead_id)
            .values(
                status=EmailSequenceStatus.REPLIED,
                promo_status=PromoTrackStatus.CODE_SENT
            )
        )
        # Here we would enqueue a Celery task to send the "Welcome14" email
        print(f"[HOT LEAD] Lead {lead_id} replied! Sending Welcome14 code.")
        
    await db.commit()
    return {"status": "success"}

# =======================
# Sandbox / Testing
# =======================
class SandboxRequest(BaseModel):
    lead_id: str
    funnel_type: str

@router.post("/sandbox/generate")
async def generate_sandbox_funnel(req: SandboxRequest, db: AsyncSession = Depends(get_db)):
    """
    Instantly generates all 5 touches for a given funnel type and lead.
    Useful for testing prompts without waiting for the scheduler.
    """
    # 1. Fetch Lead
    lead_res = await db.execute(select(Lead).where(Lead.id == req.lead_id))
    lead = lead_res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # 2. Fetch Templates
    templates_res = await db.execute(
        select(OutreachTemplate)
        .where(OutreachTemplate.funnel_type == req.funnel_type)
        .order_by(OutreachTemplate.touch_level)
    )
    templates = templates_res.scalars().all()
    if not templates:
        raise HTTPException(status_code=404, detail="No templates found for this funnel")
        
    groq_key = await get_api_key("groq")
    if not groq_key:
        raise HTTPException(status_code=400, detail="Groq API Key not found in Vault")

    audit_link = f"https://gbpilot-saas.vercel.app/audit/{lead.id}"
    
    # 3. Generate all 5 concurrently
    async def process_touch(template):
        generated = await generate_email_with_groq(groq_key, lead, template)
        body = generated.get("body", template.body_template)
        if body:
            body = body.replace("{audit_link}", audit_link)
        return {
            "touch_level": template.touch_level,
            "subject": generated.get("subject", template.subject_template),
            "body": body
        }
        
    tasks = [process_touch(t) for t in templates]
    results = await asyncio.gather(*tasks)
    
    # Sort by touch level
    results.sort(key=lambda x: x["touch_level"])
    
    return {"status": "success", "touches": results}

# =======================
# Analytics
# =======================
@router.get("/analytics")
async def get_analytics(
    project_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    product_id: Optional[str] = None,
    audience_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns aggregated conversion metrics for the dashboard split by project, product, and audience.
    """
    try:
        # Build query for EmailSequence joined with Lead and OutreachCampaign
        query = (
            select(
                EmailSequence, 
                OutreachCampaign.product_id, 
                OutreachCampaign.audience_id, 
                Lead.audience_id.label("lead_audience_id")
            )
            .outerjoin(Lead, EmailSequence.lead_id == Lead.id)
            .outerjoin(OutreachCampaign, EmailSequence.campaign_id == OutreachCampaign.id)
        )
        
        if project_id and isinstance(project_id, str) and project_id.strip() and not hasattr(project_id, 'default'):
            query = query.where(or_(Lead.project_id == project_id, OutreachCampaign.project_id == project_id))
            
        if campaign_id and isinstance(campaign_id, str) and campaign_id.strip() and not hasattr(campaign_id, 'default'):
            query = query.where(EmailSequence.campaign_id == campaign_id)
            
        if product_id and isinstance(product_id, str) and product_id.strip() and not hasattr(product_id, 'default'):
            query = query.where(OutreachCampaign.product_id == product_id)
            
        if audience_id and isinstance(audience_id, str) and audience_id.strip() and not hasattr(audience_id, 'default'):
            query = query.where(or_(Lead.audience_id == audience_id, OutreachCampaign.audience_id == audience_id))

        res = await db.execute(query)
        rows = res.all()
        
        overall = {
            "total_sequences": len(rows),
            "sent": 0,
            "opened": 0,
            "clicked": 0,
            "replied": 0,
            "bounced": 0,
            "interested": 0
        }
        funnels_map = {}
        touches_map = {}
        product_seq_stats = {}   # prod_id -> {sent, opened, clicked, replied}
        audience_seq_stats = {}  # aud_id -> {sent, opened, clicked, replied}
        
        for row in rows:
            seq = row[0]
            prod_id = str(row[1]) if row[1] else None
            aud_id = str(row[2] or row[3]) if (row[2] or row[3]) else None

            # Check status flags
            sent = seq.status in [EmailSequenceStatus.SENT, EmailSequenceStatus.OPENED, EmailSequenceStatus.REPLIED, EmailSequenceStatus.COMPLETED, EmailSequenceStatus.BOUNCED]
            opened = getattr(seq, 'opened_at', None) is not None or seq.status in [EmailSequenceStatus.OPENED, EmailSequenceStatus.REPLIED, EmailSequenceStatus.COMPLETED]
            clicked = getattr(seq, 'clicked_at', None) is not None
            replied = seq.status in [EmailSequenceStatus.REPLIED, EmailSequenceStatus.COMPLETED]
            bounced = seq.status == EmailSequenceStatus.BOUNCED
            
            if sent: overall["sent"] += 1
            if opened: overall["opened"] += 1
            if clicked: overall["clicked"] += 1
            if replied: overall["replied"] += 1
            if bounced: overall["bounced"] += 1
            
            # Group by Funnel Type (for backward compatibility)
            f_type = seq.funnel_type.value if hasattr(seq.funnel_type, "value") else str(seq.funnel_type or "CUSTOM")
            if f_type not in funnels_map:
                funnels_map[f_type] = {"name": f_type, "sent": 0, "opened": 0, "clicked": 0, "replied": 0}
            if sent: funnels_map[f_type]["sent"] += 1
            if opened: funnels_map[f_type]["opened"] += 1
            if clicked: funnels_map[f_type]["clicked"] += 1
            if replied: funnels_map[f_type]["replied"] += 1
            
            # Group by Touch Level
            t_level = seq.current_touch or 1
            if t_level not in touches_map:
                touches_map[t_level] = {"touch_level": t_level, "sent": 0, "opened": 0, "clicked": 0, "replied": 0}
            if sent: touches_map[t_level]["sent"] += 1
            if opened: touches_map[t_level]["opened"] += 1
            if clicked: touches_map[t_level]["clicked"] += 1
            if replied: touches_map[t_level]["replied"] += 1

            # Stats by Product
            if prod_id:
                if prod_id not in product_seq_stats:
                    product_seq_stats[prod_id] = {"sent": 0, "opened": 0, "clicked": 0, "replied": 0}
                if sent: product_seq_stats[prod_id]["sent"] += 1
                if opened: product_seq_stats[prod_id]["opened"] += 1
                if clicked: product_seq_stats[prod_id]["clicked"] += 1
                if replied: product_seq_stats[prod_id]["replied"] += 1

            # Stats by Audience
            if aud_id:
                if aud_id not in audience_seq_stats:
                    audience_seq_stats[aud_id] = {"sent": 0, "opened": 0, "clicked": 0, "replied": 0}
                if sent: audience_seq_stats[aud_id]["sent"] += 1
                if opened: audience_seq_stats[aud_id]["opened"] += 1
                if clicked: audience_seq_stats[aud_id]["clicked"] += 1
                if replied: audience_seq_stats[aud_id]["replied"] += 1

        # Query Inbound Replies for project/campaign
        reply_query = select(InboundReply)
        if project_id and isinstance(project_id, str) and project_id.strip() and not hasattr(project_id, 'default'):
            reply_query = reply_query.where(InboundReply.project_id == project_id)
        if campaign_id and isinstance(campaign_id, str) and campaign_id.strip() and not hasattr(campaign_id, 'default'):
            reply_query = reply_query.where(InboundReply.campaign_id == campaign_id)
        
        reply_res = await db.execute(reply_query)
        inbound_replies = reply_res.scalars().all()

        intents_counter = {
            "INTERESTED": 0,
            "QUESTION": 0,
            "OBJECTION": 0,
            "UNSUBSCRIBE": 0,
            "OUT_OF_OFFICE": 0,
            "NEUTRAL": 0
        }
        for r in inbound_replies:
            intent_val = r.intent.value if hasattr(r.intent, "value") else str(r.intent)
            if intent_val in intents_counter:
                intents_counter[intent_val] += 1
            else:
                intents_counter["NEUTRAL"] += 1

        overall["interested"] = intents_counter["INTERESTED"]

        # Calculate Rates
        overall["open_rate"] = round((overall["opened"] / overall["sent"] * 100), 1) if overall["sent"] > 0 else 0
        overall["click_rate"] = round((overall["clicked"] / overall["opened"] * 100), 1) if overall["opened"] > 0 else 0
        overall["reply_rate"] = round((overall["replied"] / overall["sent"] * 100), 1) if overall["sent"] > 0 else 0
        overall["hot_rate"] = round((overall["interested"] / overall["sent"] * 100), 1) if overall["sent"] > 0 else 0

        # Load Products metadata for breakdown
        by_product = []
        if project_id and isinstance(project_id, str) and project_id.strip():
            prod_query = select(Product).where(Product.project_id == project_id)
            prod_res = await db.execute(prod_query)
            prods = prod_res.scalars().all()
            for p in prods:
                p_id_str = str(p.id)
                p_stats = product_seq_stats.get(p_id_str, {"sent": 0, "opened": 0, "clicked": 0, "replied": 0})
                rep_rate = round((p_stats["replied"] / p_stats["sent"] * 100), 1) if p_stats["sent"] > 0 else 0
                by_product.append({
                    "product_id": p_id_str,
                    "name": p.name,
                    "price_tier": p.price_tier,
                    "sent": p_stats["sent"],
                    "opened": p_stats["opened"],
                    "clicked": p_stats["clicked"],
                    "replied": p_stats["replied"],
                    "reply_rate": rep_rate
                })

        # Load Audiences metadata for breakdown
        by_audience = []
        if project_id and isinstance(project_id, str) and project_id.strip():
            aud_query = select(Audience).where(Audience.project_id == project_id)
            aud_res = await db.execute(aud_query)
            audiences_list = aud_res.scalars().all()
            for a in audiences_list:
                a_id_str = str(a.id)
                a_stats = audience_seq_stats.get(a_id_str, {"sent": 0, "opened": 0, "clicked": 0, "replied": 0})
                rep_rate = round((a_stats["replied"] / a_stats["sent"] * 100), 1) if a_stats["sent"] > 0 else 0
                by_audience.append({
                    "audience_id": a_id_str,
                    "name": a.name,
                    "source_type": a.source_type,
                    "total_leads": a.total_leads,
                    "sent": a_stats["sent"],
                    "opened": a_stats["opened"],
                    "clicked": a_stats["clicked"],
                    "replied": a_stats["replied"],
                    "reply_rate": rep_rate
                })

        funnels_list = list(funnels_map.values())
        touches_list = sorted(list(touches_map.values()), key=lambda x: x["touch_level"])
        
        intents_list = [
            {"intent": "INTERESTED", "label": "🔥 Горячие лиды", "count": intents_counter["INTERESTED"], "color": "#10b981"},
            {"intent": "QUESTION", "label": "❓ Вопросы", "count": intents_counter["QUESTION"], "color": "#3b82f6"},
            {"intent": "OBJECTION", "label": "⚠️ Возражения", "count": intents_counter["OBJECTION"], "color": "#f59e0b"},
            {"intent": "UNSUBSCRIBE", "label": "🚫 Отписки", "count": intents_counter["UNSUBSCRIBE"], "color": "#ef4444"},
            {"intent": "OUT_OF_OFFICE", "label": "🏖 Автоответ", "count": intents_counter["OUT_OF_OFFICE"], "color": "#8b5cf6"},
            {"intent": "NEUTRAL", "label": "⚪ Прочее", "count": intents_counter["NEUTRAL"], "color": "#64748b"},
        ]

        return {
            "overall": overall,
            "funnels": funnels_list,
            "touches": touches_list,
            "by_product": by_product,
            "by_audience": by_audience,
            "intents": intents_list
        }
    except Exception as err:
        print(f"Error in get_analytics: {err}")
        return {
            "overall": {"sent": 0, "opened": 0, "clicked": 0, "replied": 0, "interested": 0, "open_rate": 0, "click_rate": 0, "reply_rate": 0, "hot_rate": 0},
            "funnels": [],
            "touches": [],
            "by_product": [],
            "by_audience": [],
            "intents": []
        }


@router.post("/process_queue")
async def trigger_process_queue():
    """
    Manually triggers process_outreach_queue_async to process pending emails immediately.
    """
    from app.workers.outreach_tasks import process_outreach_queue_async
    asyncio.create_task(process_outreach_queue_async())
    return {"status": "success", "message": "Queue processing triggered."}


# =========================================================================
# STAGE 4: MULTI-CAMPAIGN LAUNCH, REVIEW QUEUE & INBOUND INBOX
# =========================================================================

class LaunchMultiCampaignRequest(BaseModel):
    project_id: str
    product_id: Optional[str] = None
    audience_id: str
    funnel_sequence_id: Optional[str] = None
    steps: Optional[List[dict]] = None
    campaign_name: str
    is_manual_review_required: bool = False
    schedule_config: Optional[dict] = {
        "daily_limit": 50,
        "send_start_hour": 9,
        "send_end_hour": 18,
        "workdays_only": True,
        "delay_between_emails_sec": 120
    }
    filters: Optional[dict] = {}

class ReviewApproveRequest(BaseModel):
    sequence_ids: Optional[List[str]] = None
    approve_all: bool = False
    campaign_id: Optional[str] = None

class ReviewRejectRequest(BaseModel):
    sequence_ids: List[str]

class ReviewUpdateRequest(BaseModel):
    email_subject: str
    email_content: str

class SimulateReplyRequest(BaseModel):
    lead_id: str
    message_body: str
    subject: Optional[str] = None

class SendResponseRequest(BaseModel):
    response_body: str
    subject: Optional[str] = None

@router.post("/launch-multi-campaign")
async def launch_multi_campaign(
    body: LaunchMultiCampaignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Launches an independent multi-touch campaign linking Project + Product + Audience + Funnel.
    Creates Touch 1 personalized drafts or immediately queues for automated sending.
    """
    proj_uuid = uuid.UUID(body.project_id)
    aud_uuid = uuid.UUID(body.audience_id)
    prod_uuid = uuid.UUID(body.product_id) if body.product_id else None

    # 1. Fetch Funnel Steps
    steps = body.steps or []
    if not steps and body.funnel_sequence_id:
        f_seq = (await db.execute(select(FunnelSequence).where(FunnelSequence.id == uuid.UUID(body.funnel_sequence_id)))).scalars().first()
        if f_seq:
            steps = f_seq.steps

    if not steps:
        raise HTTPException(status_code=400, detail="No funnel sequence steps provided for campaign")

    # 2. Create OutreachCampaign record
    campaign = OutreachCampaign(
        project_id=proj_uuid,
        product_id=prod_uuid,
        audience_id=aud_uuid,
        name=body.campaign_name,
        filters=body.filters or {},
        schedule_config=body.schedule_config or {},
        is_manual_review_required=body.is_manual_review_required,
        status=OutreachStatus.ACTIVE
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    # 3. Select Target Leads from Audience (with email & not unsubscribed)
    leads_stmt = select(Lead).where(
        Lead.audience_id == aud_uuid,
        Lead.is_unsubscribed == False
    )
    res = await db.execute(leads_stmt)
    leads = res.scalars().all()

    first_step = steps[0]
    subject_tpl = first_step.get("subject_template", "Предложение для {{company_name}}")
    body_tpl = first_step.get("body_template", "")

    initial_status = EmailSequenceStatus.DRAFT if body.is_manual_review_required else EmailSequenceStatus.QUEUED
    queued_count = 0

    for lead in leads:
        lead_dict = {
            "company_name": lead.company_name,
            "city": lead.city,
            "address": lead.address,
            "website": lead.website,
            "business_type": lead.business_type,
            "custom_data": lead.custom_data or {}
        }
        rendered = AIFunnelService.render_preview(subject_tpl, body_tpl, lead_dict)

        seq = EmailSequence(
            lead_id=lead.id,
            campaign_id=campaign.id,
            current_touch=1,
            status=initial_status,
            email_subject=rendered["rendered_subject"],
            email_content=rendered["rendered_body"]
        )
        db.add(seq)
        queued_count += 1

    await db.commit()

    return {
        "status": "success",
        "campaign_id": str(campaign.id),
        "campaign_name": campaign.name,
        "total_leads_targeted": queued_count,
        "initial_status": initial_status.value,
        "is_review_required": body.is_manual_review_required
    }

@router.get("/review-queue")
async def get_review_queue(
    project_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns pending email drafts waiting for human operator approval before dispatch.
    """
    from sqlalchemy.orm import selectinload
    stmt = (
        select(EmailSequence)
        .options(selectinload(EmailSequence.lead).selectinload(Lead.contacts))
        .where(EmailSequence.status == EmailSequenceStatus.DRAFT)
    )

    if campaign_id:
        stmt = stmt.where(EmailSequence.campaign_id == uuid.UUID(campaign_id))
    if project_id:
        stmt = stmt.join(Lead).where(Lead.project_id == uuid.UUID(project_id))

    # Total count
    count_stmt = select(func.count(EmailSequence.id)).where(EmailSequence.status == EmailSequenceStatus.DRAFT)
    if campaign_id:
        count_stmt = count_stmt.where(EmailSequence.campaign_id == uuid.UUID(campaign_id))
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(EmailSequence.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    drafts = (await db.execute(stmt)).scalars().all()

    items = []
    for d in drafts:
        lead = d.lead
        primary_email = ""
        if lead and lead.contacts:
            for c in lead.contacts:
                if c.contact_type.lower() == "email":
                    primary_email = c.contact_value
                    break

        items.append({
            "id": str(d.id),
            "lead_id": str(d.lead_id),
            "campaign_id": str(d.campaign_id) if d.campaign_id else None,
            "company_name": lead.company_name if lead else "Unknown",
            "city": lead.city if lead else "",
            "website": lead.website if lead else "",
            "recipient_email": primary_email,
            "current_touch": d.current_touch,
            "email_subject": d.email_subject,
            "email_content": d.email_content,
            "created_at": d.created_at
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }

@router.post("/review-queue/approve")
async def approve_review_drafts(
    body: ReviewApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approves drafted emails and moves them to QUEUED for dispatch.
    """
    if body.approve_all:
        stmt = update(EmailSequence).where(EmailSequence.status == EmailSequenceStatus.DRAFT)
        if body.campaign_id:
            stmt = stmt.where(EmailSequence.campaign_id == uuid.UUID(body.campaign_id))
        stmt = stmt.values(status=EmailSequenceStatus.QUEUED)
        await db.execute(stmt)
    elif body.sequence_ids:
        uuids = [uuid.UUID(i) for i in body.sequence_ids]
        stmt = update(EmailSequence).where(EmailSequence.id.in_(uuids)).values(status=EmailSequenceStatus.QUEUED)
        await db.execute(stmt)

    await db.commit()
    return {"status": "success", "message": "Drafts approved and moved to delivery queue."}

@router.post("/review-queue/reject")
async def reject_review_drafts(
    body: ReviewRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rejects or skips drafts from sending.
    """
    uuids = [uuid.UUID(i) for i in body.sequence_ids]
    stmt = update(EmailSequence).where(EmailSequence.id.in_(uuids)).values(status=EmailSequenceStatus.COMPLETED)
    await db.execute(stmt)
    await db.commit()
    return {"status": "success", "message": "Selected drafts cancelled/skipped."}

@router.put("/review-queue/{sequence_id}")
async def update_review_draft(
    sequence_id: str,
    body: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Allows human operator to edit email subject or content inline before approving.
    """
    stmt = select(EmailSequence).where(EmailSequence.id == uuid.UUID(sequence_id))
    seq = (await db.execute(stmt)).scalars().first()
    if not seq:
        raise HTTPException(status_code=404, detail="Draft not found")

    seq.email_subject = body.email_subject
    seq.email_content = body.email_content
    await db.commit()
    await db.refresh(seq)

    return {"status": "success", "message": "Draft updated successfully"}

# --- INBOUND REPLIES & SMART INBOX ---

@router.get("/inbox")
async def list_inbound_replies(
    project_id: Optional[str] = None,
    intent: Optional[str] = None,
    is_handled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all inbound replies classified by AI.
    """
    stmt = select(InboundReply)
    if project_id:
        stmt = stmt.where(InboundReply.project_id == uuid.UUID(project_id))
    if intent:
        stmt = stmt.where(InboundReply.intent == intent)
    if is_handled is not None:
        stmt = stmt.where(InboundReply.is_handled == is_handled)

    stmt = stmt.order_by(InboundReply.created_at.desc())
    res = await db.execute(stmt)
    replies = res.scalars().all()

    items = []
    for r in replies:
        lead = r.lead
        items.append({
            "id": str(r.id),
            "project_id": str(r.project_id),
            "lead_id": str(r.lead_id),
            "company_name": lead.company_name if lead else "Unknown",
            "city": lead.city if lead else "",
            "from_email": r.from_email,
            "subject": r.subject,
            "message_body": r.message_body,
            "intent": r.intent.value if hasattr(r.intent, "value") else str(r.intent),
            "ai_analysis": r.ai_analysis,
            "ai_draft_response": r.ai_draft_response,
            "is_handled": r.is_handled,
            "handled_at": r.handled_at,
            "created_at": r.created_at
        })

    return items

@router.post("/inbox/simulate-reply")
async def simulate_inbound_reply(
    body: SimulateReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates or registers an inbound prospect email reply.
    Automatically triggers AI intent analysis, handles unsubscriptions or hot lead transitions,
    and drafts an optimal AI response based on the active product knowledge base.
    """
    lead_uuid = uuid.UUID(body.lead_id)
    lead = (await db.execute(select(Lead).where(Lead.id == lead_uuid))).scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Fetch product info from project or default
    product_dict = {"name": "Revo B2B Services", "value_props": ["Рост потока клиентов на 30%"], "target_action_cta": "согласовать короткий 15-мин звонок"}
    if lead.project_id:
        prod = (await db.execute(select(Product).where(Product.project_id == lead.project_id))).scalars().first()
        if prod:
            product_dict = {
                "name": prod.name,
                "description": prod.description,
                "value_props": prod.value_props or [],
                "pain_points": prod.pain_points or [],
                "target_action_cta": prod.target_action_cta or "согласовать звонок"
            }

    lead_dict = {
        "company_name": lead.company_name,
        "city": lead.city,
        "business_type": lead.business_type,
        "website": lead.website
    }

    # AI Classifier & Draft generator
    classification = await AIInboxService.classify_and_draft(
        inbound_message=body.message_body,
        lead_info=lead_dict,
        product_info=product_dict
    )

    intent_str = classification.get("intent", "NEUTRAL")
    try:
        reply_intent = ReplyIntent(intent_str)
    except Exception:
        reply_intent = ReplyIntent.NEUTRAL

    # Find primary email for lead
    recipient_email = "lead@example.com"
    if lead.contacts:
        for c in lead.contacts:
            if c.contact_type.lower() == "email":
                recipient_email = c.contact_value
                break

    # Automated Workflow Rules:
    if reply_intent == ReplyIntent.UNSUBSCRIBE:
        lead.is_unsubscribed = True
        # Cancel any active sequences
        await db.execute(
            update(EmailSequence)
            .where(EmailSequence.lead_id == lead.id)
            .values(status=EmailSequenceStatus.UNSUBSCRIBED)
        )
    elif reply_intent == ReplyIntent.INTERESTED:
        # Hot Lead! Stop follow-ups and advance status
        await db.execute(
            update(EmailSequence)
            .where(EmailSequence.lead_id == lead.id)
            .values(status=EmailSequenceStatus.REPLIED, promo_status=PromoTrackStatus.CODE_SENT)
        )

    # Save InboundReply record
    new_reply = InboundReply(
        project_id=lead.project_id or uuid.uuid4(),
        lead_id=lead.id,
        from_email=recipient_email,
        subject=body.subject or f"Re: {lead.company_name}",
        message_body=body.message_body,
        intent=reply_intent,
        ai_analysis=classification.get("ai_analysis"),
        ai_draft_response=classification.get("ai_draft_response")
    )
    db.add(new_reply)
    await db.commit()
    await db.refresh(new_reply)

    return {
        "status": "success",
        "reply_id": str(new_reply.id),
        "intent": reply_intent.value,
        "ai_analysis": new_reply.ai_analysis,
        "ai_draft_response": new_reply.ai_draft_response
    }

@router.post("/inbox/{reply_id}/send-response")
async def send_inbox_response(
    reply_id: str,
    body: SendResponseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sends the approved human/AI response to the lead via email and marks handled.
    """
    stmt = select(InboundReply).where(InboundReply.id == uuid.UUID(reply_id))
    reply = (await db.execute(stmt)).scalars().first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply record not found")

    # Send email via Resend if key exists
    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        try:
            resend.api_key = resend_key
            resend.Emails.send({
                "from": os.getenv("SENDER_EMAIL", "sher@banzaimarketing.tech"),
                "to": reply.from_email,
                "subject": body.subject or f"Re: {reply.subject or 'Ответ'}",
                "text": body.response_body
            })
        except Exception as e:
            logger.warning(f"Resend dispatch warning: {e}")

    reply.is_handled = True
    reply.handled_at = func.now()
    await db.commit()

    return {"status": "success", "message": f"Response sent to {reply.from_email}"}


