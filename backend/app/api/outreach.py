from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.models.lead import Lead
from pydantic import BaseModel
import os
import resend

router = APIRouter(prefix="/api/v1/outreach", tags=["Outreach"])

# Resend API Key setup (will be set in ENV, but we mock/handle it gracefully if missing)
resend.api_key = os.environ.get("RESEND_API_KEY", "re_mock_key_123")

class DraftRequest(BaseModel):
    lead_id: str

class DraftResponse(BaseModel):
    subject: str
    body: str
    audit_link: str

class SendRequest(BaseModel):
    lead_id: str
    recipient_email: str
    subject: str
    body: str

@router.post("/draft", response_model=DraftResponse)
async def generate_email_draft(request: DraftRequest, db: AsyncSession = Depends(get_db)):
    lead_res = await db.execute(select(Lead).filter(Lead.id == request.lead_id))
    lead = lead_res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    audit_link = f"https://gbpilot-saas.vercel.app/audit/{lead.id}"
    
    business_type = lead.business_type or "бизнес"
    name = lead.company_name
    rating = lead.rating or 0.0
    reviews = lead.reviews_count or 0
    city = lead.city or "вашем районе"
    
    # Legend: Market Research Analytics
    if rating < 4.5:
        subject = f"Сводка по исследованию рынка {business_type}: {name}"
        body = f"""Здравствуйте!
        
Наше агентство REVO Data проводит квартальное исследование рынка {business_type} в {city}. 
При анализе данных Google Карт мы обратили внимание на профиль вашей компании ({name}).

Мы заметили, что ваш текущий рейтинг ({rating} ⭐️ на основе {reviews} отзывов) находится в зоне риска по сравнению с конкурентами в вашем районе. Алгоритмы поиска активно пессимизируют профили с такими показателями, из-за чего вы можете недополучать до 35% потенциальных клиентов.

Чтобы быть полезными, мы сгенерировали для вас бесплатный аналитический мини-отчет. Он показывает, какие именно факторы сейчас тянут ваш профиль вниз, и что нужно исправить.

🔗 Посмотреть ваш конфиденциальный отчет можно здесь:
{audit_link}

Буду рад ответить на любые вопросы, если они возникнут после просмотра отчета.

С уважением,
Отдел аналитики
REVO Master Data
"""
    else:
        subject = f"Аналитика конкурентов для {name} ({business_type})"
        body = f"""Здравствуйте!
        
Наше агентство REVO Data проводит анализ рынка локального бизнеса в {city}. 
Мы изучили профиль вашей компании ({name}) на Google Картах и хотим отметить отличную работу: ваш рейтинг ({rating} ⭐️) говорит о высоком качестве сервиса!

Однако мы заметили несколько уязвимостей в технической настройке профиля (отсутствие скрытых категорий и свежих обновлений), которые позволяют конкурентам перехватывать часть вашего горячего трафика. 

Мы составили для вас персональный аналитический отчет. В нем показано, как с помощью ИИ и пары кликов вы можете "дожать" выдачу и закрепиться на первых местах.

🔗 Ознакомьтесь с отчетом здесь:
{audit_link}

Отличного дня и стабильного роста!

С уважением,
Отдел аналитики
REVO Master Data
"""

    return DraftResponse(
        subject=subject,
        body=body,
        audit_link=audit_link
    )

@router.post("/send")
async def send_outreach_email(request: SendRequest, db: AsyncSession = Depends(get_db)):
    try:
        from app.models.vault import VaultKey
        from sqlalchemy import select
        
        # 1. Try DB Vault
        resend_vault_res = await db.execute(select(VaultKey).filter(VaultKey.provider == "resend"))
        resend_vault = resend_vault_res.scalar_one_or_none()
        if resend_vault and resend_vault.api_key_encrypted:
            resend.api_key = resend_vault.api_key_encrypted
        else:
            # 2. Try OS Env
            resend.api_key = os.environ.get("RESEND_API_KEY", "re_mock_key_123")
            
        if resend.api_key == "re_mock_key_123":
            print(f"[MOCK SEND] Email to {request.recipient_email} via Resend. Subject: {request.subject}")
            return {"status": "success", "message": "Simulated sending email (Missing API Key)", "id": "mock_123"}
            
        response = resend.Emails.send({
            "from": "REVO Analytics <analytics@revo-masterdata.com>",
            "to": [request.recipient_email],
            "subject": request.subject,
            "html": request.body.replace(chr(10), "<br>") # Convert newlines to HTML breaks
        })
        
        # Log this action to lead history in real app
        
        return {"status": "success", "message": "Email sent via Resend", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
