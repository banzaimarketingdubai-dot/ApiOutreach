import json
import logging
import re
import httpx
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

INBOX_CLASSIFIER_PROMPT = """
You are an expert B2B SDR and Cold Outreach Reply Specialist.
Your mission is to analyze an incoming email reply from a prospective B2B client and:
1. Classify the intent into one of these strict categories:
   - INTERESTED: Hot lead wanting demo, pricing, meeting, audit, or asking to connect.
   - OBJECTION: Expresses concern (too expensive, no time, using competitor, bad timing).
   - QUESTION: Asking for more information or clarification.
   - UNSUBSCRIBE: Asking to stop emails, not interested, remove from list, angry refusal.
   - OUT_OF_OFFICE: Auto-responder, vacation notice, sick leave.
   - NEUTRAL: Unclear response.

2. Provide a 1-sentence analytical summary ("ai_analysis").
3. If the intent is INTERESTED, OBJECTION, or QUESTION: Draft a polite, concise (under 80 words) and high-converting response ("ai_draft_response") tailored to the Product/Offer details.
   If UNSUBSCRIBE or OUT_OF_OFFICE: Provide a brief polite closing or leave null.

Output STRICTLY in valid JSON:
{
  "intent": "INTERESTED" | "OBJECTION" | "QUESTION" | "UNSUBSCRIBE" | "OUT_OF_OFFICE" | "NEUTRAL",
  "ai_analysis": "Brief explanation of prospect's intent",
  "ai_draft_response": "Suggested reply text"
}
"""

class AIInboxService:

    @staticmethod
    async def classify_and_draft(
        inbound_message: str,
        lead_info: Dict[str, Any],
        product_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify inbound email and generate smart reply draft using Gemini / Grok.
        """
        prompt = f"""
LEAD / COMPANY INFO:
- Company Name: {lead_info.get('company_name', 'Client')}
- City: {lead_info.get('city', '')}
- Business Type: {lead_info.get('business_type', '')}
- Website: {lead_info.get('website', '')}

PRODUCT / OFFER DETAILS:
- Product Name: {product_info.get('name', 'Наш сервис')}
- Description: {product_info.get('description', '')}
- Key USPs: {json.dumps(product_info.get('value_props', []), ensure_ascii=False)}
- Pain Points Solved: {json.dumps(product_info.get('pain_points', []), ensure_ascii=False)}
- Target Action (CTA): {product_info.get('target_action_cta', 'Согласовать время звонка')}

INCOMING EMAIL MESSAGE FROM PROSPECT:
\"\"\"
{inbound_message}
\"\"\"

Analyze the email and respond with the JSON structure.
        """

        from app.services.vault_helper import get_api_key
        gemini_key = await get_api_key("gemini")

        if gemini_key:
            for model in ["gemini-3.1-pro", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
                try:
                    result = await AIInboxService._call_gemini(gemini_key, model, prompt)
                    if result and "intent" in result:
                        return result
                except Exception as e:
                    logger.warning(f"Inbox Gemini error with {model}: {e}")

        # Grok fallback
        if settings.GROK_API_KEY:
            try:
                result = await AIInboxService._call_grok(settings.GROK_API_KEY, prompt)
                if result and "intent" in result:
                    return result
            except Exception as e:
                logger.warning(f"Inbox Grok error: {e}")

        # Smart rule-based fallback
        return AIInboxService._smart_heuristic_fallback(inbound_message, lead_info, product_info)

    @staticmethod
    async def _call_gemini(api_key: str, model: str, prompt: str) -> Dict[str, Any]:
        from app.services.rate_limiter import wait_for_gemini_capacity
        await wait_for_gemini_capacity()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": INBOX_CLASSIFIER_PROMPT + "\n\n" + prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

    @staticmethod
    async def _call_grok(api_key: str, prompt: str) -> Dict[str, Any]:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": INBOX_CLASSIFIER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                text = re.sub(r"^```json\s*", "", text.strip())
                text = re.sub(r"\s*```$", "", text.strip())
                return json.loads(text)
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

    @staticmethod
    def _smart_heuristic_fallback(text: str, lead_info: dict, product_info: dict) -> dict:
        lower = text.lower()
        company = lead_info.get("company_name", "коллеги")
        cta = product_info.get("target_action_cta", "созвониться на 10 минут")

        # Check Unsubscribe
        if any(w in lower for w in ["отписаться", "не пишите", "удалите", "отпишите", "спам", "unsubscribe", "stop", "not interested", "не интересно"]):
            return {
                "intent": "UNSUBSCRIBE",
                "ai_analysis": "Клиент попросил исключить компанию из рассылки.",
                "ai_draft_response": f"Понял вас. Исключил {company} из нашего списка. Прошу прощения за беспокойство!"
            }

        # Check Out of office
        if any(w in lower for w in ["автоответ", "в отпуске", "out of office", "автоматический", "вернусь"]):
            return {
                "intent": "OUT_OF_OFFICE",
                "ai_analysis": "Автоответчик: сотрудник отсутствует на рабочем месте.",
                "ai_draft_response": None
            }

        # Check Interest
        if any(w in lower for w in ["давайте", "интересно", "пришлите", "согласен", "сколько стоит", "подробнее", "демо", "расскажите", "цена", "стоимость", "yes", "interested"]):
            return {
                "intent": "INTERESTED",
                "ai_analysis": "Клиент выразил прямой интерес или запросил детали/условия.",
                "ai_draft_response": (
                    f"Здравствуйте! Отлично. Подскажите, будет ли вам удобно {cta} "
                    f"в первой половине завтрашнего дня, или удобнее в четверг?"
                )
            }

        # Default Objection / Question
        return {
            "intent": "QUESTION",
            "ai_analysis": "Клиент задал уточняющий вопрос или оставил комментарий.",
            "ai_draft_response": (
                f"Здравствуйте! Благодарю за ответ. Мы разработали решение специально под задачи компаний уровня {company}. "
                f"Предлагаю кратко обсудить детали, когда вам будет удобнее?"
            )
        }
