import asyncio
import logging
import traceback
import resend
from datetime import datetime, timedelta
from typing import Optional
import os

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from celery import shared_task

from app.db.session import AsyncSessionLocal
from app.models.email_sequence import EmailSequence, EmailSequenceStatus, FunnelType, OutreachTemplate
from app.models.lead import Lead
from app.services.vault_helper import get_api_key

logger = logging.getLogger(__name__)

async def generate_email_with_groq(groq_key: str, lead: Lead, template: OutreachTemplate) -> dict:
    """Uses Groq to generate customized subject and body."""
    import httpx
    import json
    
    system_instruction = f"""
    You are an expert B2B SaaS copywriter. Your goal is to write highly converting outreach messages.
    Generate a JSON response containing 'subject' and 'body' (HTML format).
    Context/Instructions: {template.ai_prompt_context or 'Make it personalized and engaging.'}
    Subject Template Hint: {template.subject_template}
    Body Template Hint: {template.body_template}
    
    Lead Data:
    Company Name: {lead.company_name}
    Niche: {lead.business_type}
    City: {lead.city}
    Rating: {lead.rating} (from {lead.reviews_count} reviews)
    
    You MUST return a valid JSON object matching this schema exactly:
    {{"subject": "str", "body": "str"}}
    """
    
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Напиши персонализированное холодное сообщение для {lead.company_name}."}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url, 
            json=payload, 
            headers={"Authorization": f"Bearer {groq_key}"}
        )
        
        if resp.status_code != 200:
            logger.error(f"Groq API Error: {resp.text}")
            return {"subject": template.subject_template, "body": template.body_template}
            
        raw_json = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(raw_json)
        return data

async def send_resend_email(resend_key: str, to_email: str, subject: str, html_body: str) -> bool:
    resend.api_key = resend_key
    
    try:
        r = resend.Emails.send({
            "from": os.getenv("SENDER_EMAIL", "onboarding@resend.dev"),
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
        logger.info(f"Sent email to {to_email}. Resend ID: {r.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

async def process_outreach_queue_async():
    async with AsyncSessionLocal() as db:
        # Find all sequences that are ready to send
        # 1. ACTIVE and next_send_date <= NOW
        # 2. QUEUED (Custom overrides ready immediately)
        query = select(EmailSequence, Lead).join(Lead).where(
            and_(
                Lead.is_unsubscribed == False,
                (
                    (EmailSequence.status == EmailSequenceStatus.QUEUED) |
                    (
                        (EmailSequence.status == EmailSequenceStatus.ACTIVE) &
                        (EmailSequence.next_send_date <= func.now())
                    )
                )
            )
        ).limit(50) # Limit batch to 50 for rate limiting
        
        from sqlalchemy.sql import func
        # Wait, func.now() in python needs to be handled via sqlalchemy, we can just use datetime.now(timezone.utc)
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        
        query = select(EmailSequence, Lead).join(Lead).where(
            and_(
                Lead.is_unsubscribed == False,
                (
                    (EmailSequence.status == EmailSequenceStatus.QUEUED) |
                    (
                        (EmailSequence.status == EmailSequenceStatus.ACTIVE) &
                        (EmailSequence.next_send_date <= now_utc)
                    )
                )
            )
        ).limit(50)

        res = await db.execute(query)
        sequence_lead_pairs = res.all()
        
        if not sequence_lead_pairs:
            logger.info("Outreach Queue: No pending sequences found.")
            return

        groq_key = await get_api_key("groq")
        resend_key = os.getenv("RESEND_API_KEY")
        
        if not resend_key:
            logger.error("Outreach Queue: RESEND_API_KEY missing.")
            return

        for seq, lead in sequence_lead_pairs:
            # 1. Determine Subject and Body
            subject = seq.email_subject
            body = seq.email_content
            
            if seq.funnel_type != FunnelType.CUSTOM and (not subject or not body):
                # Automated Funnel: Need to generate content from template
                template_res = await db.execute(
                    select(OutreachTemplate).where(
                        OutreachTemplate.funnel_type == seq.funnel_type,
                        OutreachTemplate.touch_level == seq.current_touch
                    )
                )
                template = template_res.scalar_one_or_none()
                
                if template:
                    if groq_key:
                        generated = await generate_email_with_groq(groq_key, lead, template)
                        subject = generated.get("subject", template.subject_template)
                        body = generated.get("body", template.body_template)
                    else:
                        subject = template.subject_template
                        body = template.body_template
                else:
                    logger.warning(f"No template found for Funnel {seq.funnel_type}, Touch {seq.current_touch}")
                    continue

            # 2. Inject Unsubscribe Link & Audit Link if needed
            unsub_link = f"https://api.revo-masterdata.com/api/v1/outreach/webhooks/unsubscribe?lead_id={lead.id}"
            audit_link = f"https://gbpilot-saas.vercel.app/audit/{lead.id}"
            
            if body:
                body = body.replace("{audit_link}", audit_link)
                # Append unsubscribe link
                body += f"<br><br><p style='font-size: 11px; color: #9ca3af;'><a href='{unsub_link}'>Отписаться</a></p>"

            # 3. Find Recipient Email
            recipient_email = None
            if lead.contacts:
                for c in lead.contacts:
                    if c.contact_type == 'email':
                        recipient_email = c.contact_value
                        break
            if not recipient_email and lead.email: # if lead has direct email field
                recipient_email = lead.email
                
            if not recipient_email:
                logger.warning(f"No email found for Lead {lead.id}. Skipping.")
                # Mark as completed or bounced? Let's just pause it.
                seq.status = EmailSequenceStatus.PAUSED
                await db.commit()
                continue

            # 4. Send Email via Resend
            success = await send_resend_email(resend_key, recipient_email, subject, body)
            
            # 5. Update Sequence State
            if success:
                if seq.funnel_type == FunnelType.CUSTOM:
                    seq.status = EmailSequenceStatus.COMPLETED
                else:
                    seq.current_touch += 1
                    if seq.current_touch > 5:
                        seq.status = EmailSequenceStatus.COMPLETED
                    else:
                        seq.status = EmailSequenceStatus.ACTIVE
                        # Calculate delay (e.g., Touch 2 is 2 days later, Touch 3 is 4 days later)
                        days_delay = 2 if seq.current_touch == 2 else 4
                        seq.next_send_date = now_utc + timedelta(days=days_delay)
                        # Clear old content so it regenerates next time
                        seq.email_subject = None
                        seq.email_content = None
            else:
                seq.status = EmailSequenceStatus.PAUSED
                
            await db.commit()

            # Rate Limit for Resend (e.g. 2-3 per min)
            await asyncio.sleep(5)

@shared_task
def process_outreach_queue():
    """
    Celery task that runs periodically to process pending outreach emails.
    """
    logger.info("Starting process_outreach_queue task...")
    try:
        asyncio.run(process_outreach_queue_async())
        logger.info("Finished process_outreach_queue task.")
    except Exception as e:
        logger.error(f"Error in process_outreach_queue: {e}")
        logger.error(traceback.format_exc())
