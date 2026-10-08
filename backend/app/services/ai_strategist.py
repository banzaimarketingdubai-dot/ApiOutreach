import json
import logging
import httpx
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

STRATEGIST_SYSTEM_PROMPT = """
You are an expert B2B Outreach Campaign Strategist and Data Architect for 'Revo Outreach'.
Your job is to analyze the user's high-level goal and generate a complete, structured Campaign JSON Configuration.

You must respond STRICTLY with valid JSON in the following format:
{
  "campaign_name": "Short descriptive campaign title",
  "target_geo": "Target City or Country",
  "target_niches": ["Niche 1", "Niche 2"],
  "search_queries": ["Query 1 in target geo", "Query 2 in target geo"],
  "max_places": 100,
  "sources": ["gmaps"],
  "custom_variables": [
    {
      "key": "snake_case_variable_name",
      "description": "Clear instructions for LLM extracting this variable from company website text",
      "variable_type": "boolean"
    }
  ],
  "scoring_rules": {
    "missing_website_penalty": 10,
    "low_rating_penalty": 15,
    "low_reviews_penalty": 20
  },
  "recommended_outreach_angle": "Strategic proposal for how to pitch the leads",
  "reasoning": "Explanation of why these queries and custom variables were chosen"
}
"""

class AIStrategistService:
    @staticmethod
    async def generate_campaign_config(user_goal: str, geo: str = "Dubai", additional_notes: str = "") -> Dict[str, Any]:
        prompt = f"""
Goal: {user_goal}
Target GEO: {geo}
Additional Notes: {additional_notes}

Design the optimal scraping campaign & custom variables to extract from company websites to identify high-value leads.
        """

        # Attempt calling Gemini API first, then Grok as fallback or alternative
        from app.services.vault_helper import get_api_key
        gemini_key = await get_api_key("gemini")
        
        if gemini_key:
            for model in ["gemini-1.5-pro", "gemini-1.5-flash"]:
                try:
                    result = await AIStrategistService._call_gemini_api(gemini_key, model, prompt)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Gemini API call failed with model {model}: {e}")

        # Fallback to Grok if available
        if settings.GROK_API_KEY:
            try:
                result = await AIStrategistService._call_grok_api(settings.GROK_API_KEY, prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Grok API call failed: {e}")

        # Mock / Rule-based Fallback if API keys are missing or failed
        logger.info("Using internal fallback for AI Strategist configuration.")
        return AIStrategistService._generate_smart_mock_config(user_goal, geo)

    @staticmethod
    async def _call_gemini_api(api_key: str, model: str, prompt: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": STRATEGIST_SYSTEM_PROMPT + "\n\n" + prompt}]}
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
        return None

    @staticmethod
    async def _call_grok_api(api_key: str, prompt: str) -> Dict[str, Any]:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": STRATEGIST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                # Clean Markdown backticks if present
                clean_text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
        return None

    @staticmethod
    def _generate_smart_mock_config(user_goal: str, geo: str) -> Dict[str, Any]:
        return {
            "campaign_name": f"Outreach Campaign: {user_goal[:30]} ({geo})",
            "target_geo": geo,
            "target_niches": ["Dental Clinics", "Aesthetic Clinics", "Medical Centers"],
            "search_queries": [
                f"Dental Clinic in {geo}",
                f"Aesthetic Clinic in {geo}",
                f"Medical Center in {geo}"
            ],
            "sources": ["gmaps"],
            "custom_variables": [
                {
                    "key": "has_online_booking",
                    "description": "Does the company website feature an online booking system or widget?",
                    "variable_type": "boolean"
                },
                {
                    "key": "uses_crm_chat",
                    "description": "Does the site have a live chat widget (e.g. WhatsApp button, Intercom, JivoChat)?",
                    "variable_type": "boolean"
                },
                {
                    "key": "primary_services",
                    "description": "List 2-3 main high-ticket services mentioned on the site",
                    "variable_type": "string"
                }
            ],
            "scoring_rules": {
                "missing_website_penalty": 10,
                "low_rating_penalty": 15,
                "low_reviews_penalty": 20
            },
            "recommended_outreach_angle": f"Target businesses in {geo} with missing automated booking software to pitch Revo automation solutions.",
            "reasoning": "Selected clinics in target area due to high client value and potential for digital transformation."
        }
