import json
import logging
import re
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

FUNNEL_STUDIO_SYSTEM_PROMPT = """
You are an Elite B2B Cold Email Copywriter and Sales Sequence Architect.
Your task is to generate a high-converting, personalized multi-touch cold email sequence (Funnel) for an outreach campaign.

Copywriting Philosophy:
1. Short, conversational, human (under 120 words per email). Avoid corporate fluff, robotic jargon, and spam buzzwords.
2. StoryBrand & Pain-Agitate-Solve framework: The prospect is the HERO; our product/service is the GUIDE with a simple plan.
3. Every step has a clear, low-friction Call to Action (e.g. "Стоит прислать 2-минутное демо?", "Актуален ли для вас этот вопрос в этом месяце?").
4. Personalization tags: ALWAYS use placeholders where appropriate:
   - {{company_name}} : Name of the prospect's company
   - {{city}} : City of operation
   - {{website}} : Their website URL
   - {{business_type}} : Their niche / category
   - {{custom_data.<var>}} : Any custom enriched variable (e.g. {{custom_data.pain_point}})

You must respond STRICTLY with a valid JSON object matching this schema:
{
  "funnel_name": "Short descriptive funnel title",
  "target_audience_summary": "1-sentence summary of who this sequence targets and why",
  "recommended_cadence_days": [0, 2, 5],
  "steps": [
    {
      "step_number": 1,
      "step_name": "Хук и главная боль (Hook & Pain Point)",
      "delay_days": 0,
      "subject_template": "Вопрос по {{company_name}}",
      "subject_variants": ["{{company_name}} + вопрос по клиентам", "{{city}}: для {{company_name}}"],
      "body_template": "Здравствуйте!\n\nОбратил внимание на {{company_name}} в г. {{city}}...\n\nСтоит прислать короткие детали?",
      "rationale": "Короткий искренний хук с фокусом на боли клиента.",
      "target_cta": "Начать диалог без давления"
    }
  ]
}
"""

class AIFunnelService:

    @staticmethod
    async def generate_funnel_sequence(
        product_info: Dict[str, Any],
        audience_info: Dict[str, Any],
        touches_count: int = 3,
        tone_of_voice: str = "Деловой и эмпатичный",
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a multi-touch sequence using Gemini API (or Grok fallback).
        """
        user_prompt = f"""
PRODUCT / OFFER INFORMATION:
- Name: {product_info.get('name', 'B2B Product')}
- Description: {product_info.get('description', 'B2B Solutions')}
- Ideal Customer Profile (ICP): {product_info.get('target_audience_icp', 'Business owners')}
- Key Pain Points Solved: {json.dumps(product_info.get('pain_points', []), ensure_ascii=False)}
- Key Value Propositions / USPs: {json.dumps(product_info.get('value_props', []), ensure_ascii=False)}
- Target Action (CTA Goal): {product_info.get('target_action_cta', 'Get a response / schedule demo')}
- Pricing / Offer Details: {product_info.get('pricing_details', '')}

AUDIENCE / TARGET SEGMENT:
- Audience Name: {audience_info.get('name', 'B2B Leads')}
- Audience Description: {audience_info.get('description', '')}
- Source Type: {audience_info.get('source_type', 'Google Maps')}
- Available Custom Fields: {json.dumps(audience_info.get('custom_fields_schema', []), ensure_ascii=False)}

CONFIGURATION:
- Number of Touches: {touches_count}
- Tone of Voice: {tone_of_voice}
- Custom Instructions / Angles: {custom_instructions or "None"}

Generate exactly {touches_count} sequence steps in Russian (or matching the product context).
Each follow-up must naturally refer to the previous touch (e.g. using 'Re: ' for subject lines from step 2).
        """

        from app.services.vault_helper import get_api_key
        gemini_key = await get_api_key("gemini")

        errors = []
        if gemini_key:
            for model in ["gemini-3.1-pro", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
                try:
                    result = await AIFunnelService._call_gemini_api(gemini_key, model, user_prompt)
                    if result and "steps" in result:
                        return result
                except Exception as e:
                    errors.append(f"Gemini {model}: {e}")
                    logger.warning(f"Funnel generation error with {model}: {e}")

        # Fallback to Grok
        if settings.GROK_API_KEY:
            try:
                result = await AIFunnelService._call_grok_api(settings.GROK_API_KEY, user_prompt)
                if result and "steps" in result:
                    return result
            except Exception as e:
                errors.append(f"Grok: {e}")
                logger.warning(f"Funnel generation error with Grok: {e}")

        # Smart rule-based fallback if APIs fail or keys are not available
        logger.info("Using smart rule-based generator for AI Funnel sequence.")
        return AIFunnelService._generate_smart_fallback_funnel(product_info, audience_info, touches_count)

    @staticmethod
    async def _call_gemini_api(api_key: str, model: str, prompt: str) -> Dict[str, Any]:
        from app.services.rate_limiter import wait_for_gemini_capacity
        await wait_for_gemini_capacity()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": FUNNEL_STUDIO_SYSTEM_PROMPT + "\n\n" + prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.3,
                "response_mime_type": "application/json"
            }
        }
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

    @staticmethod
    async def _call_grok_api(api_key: str, prompt: str) -> Dict[str, Any]:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": FUNNEL_STUDIO_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                # Clean json codeblocks if any
                text = re.sub(r"^```json\s*", "", text.strip())
                text = re.sub(r"\s*```$", "", text.strip())
                return json.loads(text)
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

    @staticmethod
    def _generate_smart_fallback_funnel(product_info: dict, audience_info: dict, count: int) -> dict:
        prod_name = product_info.get("name", "Решение для бизнеса")
        cta = product_info.get("target_action_cta", "обсудить 15 минут в Zoom")
        
        pain = "привлечением и удержанием платежеспособных клиентов"
        pains = product_info.get("pain_points") or []
        if pains and len(pains) > 0:
            pain = pains[0]

        usp = "увеличить поток заявок на 30-40% без раздувания бюджета"
        usps = product_info.get("value_props") or []
        if usps and len(usps) > 0:
            usp = usps[0]

        steps = [
            {
                "step_number": 1,
                "step_name": "Хук и главная боль",
                "delay_days": 0,
                "subject_template": "Вопрос по клиентам в {{company_name}} (г. {{city}})",
                "subject_variants": [
                    "{{company_name}} + {{city}}",
                    "Вопрос руководителю {{company_name}}"
                ],
                "body_template": (
                    "Здравствуйте!\n\n"
                    "Обратил внимание на ваш бизнес {{company_name}} в г. {{city}}.\n\n"
                    f"Часто компании вашей ниши сталкиваются с проблемой: {pain}.\n\n"
                    f"Мы разработали {prod_name}, которое позволяет {usp}.\n\n"
                    f"Подскажите, актуальна ли сейчас эта задача для вашей команды?"
                ),
                "rationale": "Короткий хук с фокусом на боли и низким порогом входа в диалог.",
                "target_cta": "Проверить интерес"
            },
            {
                "step_number": 2,
                "step_name": "Социальное доказательство и кейс",
                "delay_days": 2,
                "subject_template": "Re: Вопрос по клиентам в {{company_name}} (г. {{city}})",
                "subject_variants": ["Re: {{company_name}}"],
                "body_template": (
                    "Здравствуйте! Хотел кратко дополнить свое предыдущее письмо.\n\n"
                    f"Недавно внедрили {prod_name} для аналогичного проекта — за первые 3 недели удалось закрыть вопрос с {pain} и получить ощутимый прирост выручки.\n\n"
                    f"Могу показать 3-минутный разбор или скриншоты внедрения. Будет интересно взглянуть?"
                ),
                "rationale": "Снятие скепсиса через социальное доказательство и конкретный результат.",
                "target_cta": "Предложить ознакомиться с кейсом"
            },
            {
                "step_number": 3,
                "step_name": "Финальный брейкап и вежливый выход",
                "delay_days": 5,
                "subject_template": "Re: Вопрос по клиентам в {{company_name}} (г. {{city}})",
                "subject_variants": ["Финальный вопрос для {{company_name}}"],
                "body_template": (
                    "Здравствуйте!\n\n"
                    "Понимаю, что сейчас у вас может быть высокий темп и другие приоритеты, поэтому не буду больше отвлекать письмами.\n\n"
                    f"Если вопрос {pain} станет актуален позже — просто напишите ответ на это письмо, и мы с радостью подключимся.\n\n"
                    "Желаю отличных результатов и развития {{company_name}}!"
                ),
                "rationale": "Создание эффекта FOMO через вежливый выход из переписки без навязчивости.",
                "target_cta": "Финальный импульс к ответу"
            }
        ]

        return {
            "funnel_name": f"Воронка касаний: {prod_name} для {audience_info.get('name', 'Аудитории')}",
            "target_audience_summary": f"Последовательность для квалификации лидов из аудитории {audience_info.get('name', 'Аудитории')}",
            "recommended_cadence_days": [0, 2, 5][:count],
            "steps": steps[:count]
        }

    @staticmethod
    def render_preview(subject_template: str, body_template: str, lead_dict: dict) -> dict:
        """
        Replaces {{placeholders}} with real data from a lead record.
        """
        def replace_match(match):
            key = match.group(1).strip()
            
            # Direct lead attributes
            if key in lead_dict and lead_dict[key] is not None:
                return str(lead_dict[key])
            
            # Custom data nested attributes e.g. {{custom_data.pain_point}}
            if key.startswith("custom_data."):
                sub_key = key.split(".", 1)[1]
                custom = lead_dict.get("custom_data") or {}
                if sub_key in custom and custom[sub_key] is not None:
                    return str(custom[sub_key])
            
            # Special fallbacks
            if key == "company_name":
                return lead_dict.get("company_name") or "Коллеги"
            if key == "city":
                return lead_dict.get("city") or "вашем городе"
            if key == "website":
                return lead_dict.get("website") or ""

            return match.group(0)

        rendered_subject = re.sub(r"\{\{([^\}]+)\}\}", replace_match, subject_template or "")
        rendered_body = re.sub(r"\{\{([^\}]+)\}\}", replace_match, body_template or "")

        return {
            "rendered_subject": rendered_subject,
            "rendered_body": rendered_body
        }
