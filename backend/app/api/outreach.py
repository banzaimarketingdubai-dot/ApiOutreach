from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel
import os
import resend

from app.api.deps import get_db
from app.models.lead import Lead
from app.models.outreach_campaign import OutreachCampaign, OutreachStatus
from app.models.email_sequence import EmailSequence, EmailSequenceStatus, PromoTrackStatus

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
        "model": "llama-3.1-8b-instant",
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
            .values(status=EmailSequenceStatus.OPENED)
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
