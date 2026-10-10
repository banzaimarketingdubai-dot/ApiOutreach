import json
import logging
import httpx
import trafilatura
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIEnrichmentService:
    @staticmethod
    async def extract_website_text(url: str) -> Tuple[str, str]:
        """Download web page and extract clean text content. Returns (text, error_message)."""
        if not url:
            return "", "Empty URL"
            
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        # Social Media & CRM Filter
        social_domains = ['instagram.com', 'facebook.com', 't.me', 'vk.com', 'linkedin.com', 'twitter.com', 'x.com', 'fresha.com', 'booksy.com', 'calendly.com', 'dikidi.net', 'wa.me', 'alteg.io', 'yclients.com']
        if any(domain in url.lower() for domain in social_domains):
            return "", f"Social Media or CRM link ignored. Specialized scraper required."
            
        try:
            # 1. Try Jina Reader API first (handles JS, Headless Chrome, Cloudflare)
            async with httpx.AsyncClient(timeout=15.0) as client:
                jina_url = f"https://r.jina.ai/{url}"
                resp = await client.get(jina_url)
                if resp.status_code == 200 and len(resp.text) > 100:
                    return resp.text[:4000], ""
        except Exception as e:
            logger.warning(f"Jina Reader failed for {url}: {e}")
            
        try:
            # 2. Fallback to basic HTTP request if Jina fails
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if resp.status_code == 200:
                    text = trafilatura.extract(resp.text)
                    if text:
                        return text[:4000], ""
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()
                    clean_text = soup.get_text(separator=' ', strip=True)[:4000]
                    if clean_text:
                        return clean_text, ""
                    return "", "Website returned empty HTML (probably JS-rendered SPA)"
                return "", f"Website returned status code {resp.status_code}"
        except Exception as e:
            return "", f"Connection failed or Timeout: {str(e)}"
            
        return "", "Unknown extraction error"

    @staticmethod
    async def batch_enrich_sites(
        site_batches: List[Dict[str, str]], # List of {"lead_id": str, "website": str, "text": str}
        custom_vars: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Batches 5-10 website texts into ONE LLM prompt.
        Returns a dict mapping lead_id -> extracted custom_data dict.
        """
        if not site_batches or not custom_vars:
            return {}

        prompt_data = []
        for idx, item in enumerate(site_batches, 1):
            prompt_data.append(f"--- SITE #{idx} [ID: {item['lead_id']}] ({item['website']}) ---\n{item['text'][:2000]}\n")

        vars_desc = json.dumps(custom_vars, indent=2)

        sys_prompt = f"""
You are an AI Data Enrichment Agent.
Analyze the text of the websites provided below and extract the requested variables for EACH website.

Custom Variables to extract:
{vars_desc}

Respond STRICTLY with a JSON array where each object has:
- "lead_id": string ID matching the site header
- "extracted_data": object containing the key-value pairs for the requested custom variables.

Example Output:
[
  {{
    "lead_id": "uuid-1",
    "extracted_data": {{
      "has_online_booking": true,
      "uses_crm_chat": false
    }}
  }}
]
"""

        full_prompt = sys_prompt + "\n\n" + "\n".join(prompt_data)

        # Call Gemini or Grok
        from app.services.vault_helper import get_api_key
        gemini_key = await get_api_key("gemini")
        if gemini_key:
            for model in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro"]:
                try:
                    res = await AIEnrichmentService._call_gemini_batch(gemini_key, model, full_prompt)
                    if res:
                        return res
                except Exception as e:
                    logger.warning(f"Batch enrichment Gemini call failed: {e}")

        # Fallback to local heuristic extraction if API fails
        logger.info("Using heuristic fallback for site batch enrichment.")
        result_map = {}
        for item in site_batches:
            heuristic_data = {}
            text_lower = item["text"].lower()
            for v in custom_vars:
                k = v.get("key")
                if "booking" in k or "appointment" in k:
                    heuristic_data[k] = any(word in text_lower for word in ["book", "appointment", "schedule", "запись"])
                elif "chat" in k or "crm" in k or "whatsapp" in k:
                    heuristic_data[k] = any(word in text_lower for word in ["whatsapp", "chat", "contact us", "написать"])
                else:
                    heuristic_data[k] = None
            result_map[item["lead_id"]] = heuristic_data
        return result_map

    @staticmethod
    async def _call_gemini_batch(api_key: str, model: str, prompt: str) -> Dict[str, Dict[str, Any]]:
        from app.services.rate_limiter import wait_for_gemini_capacity
        await wait_for_gemini_capacity()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
        }
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                raw_json = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                arr = json.loads(raw_json)
                out = {}
                for obj in arr:
                    out[obj["lead_id"]] = obj.get("extracted_data", {})
                return out
        return None

    @staticmethod
    async def generate_dry_run_emails(prompt_template: str, leads_data: List[Dict[str, Any]]) -> List[str]:
        """
        Takes a prompt template containing {{variables}} and generates emails using Gemini for a batch of leads.
        """
        from app.services.vault_helper import get_api_key
        api_key = await get_api_key("gemini")
        
        if not api_key:
            return [f"[Mock generated email based on '{prompt_template}']\nHello {l.get('company_name')}, we see you are in {l.get('city')}..." for l in leads_data]

        results = []
        model = "gemini-3.8-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            for lead in leads_data:
                from app.services.rate_limiter import wait_for_gemini_capacity
                await wait_for_gemini_capacity()
                
                # Substitute variables in prompt
                prompt = prompt_template
                for k, v in lead.items():
                    if v is not None:
                        prompt = prompt.replace(f"{{{{{k}}}}}", str(v))
                
                # If custom_data exists, substitute those too
                if lead.get("custom_data"):
                    for k, v in lead["custom_data"].items():
                        prompt = prompt.replace(f"{{{{{k}}}}}", str(v))

                sys_msg = "You are an expert B2B copywriter. Write the email exactly as requested by the prompt. Output only the email text, no pleasantries."
                
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": sys_msg + "\n\n" + prompt}]}],
                    "generationConfig": {"temperature": 0.4}
                }
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        results.append(text.strip())
                    else:
                        results.append(f"[Error: API returned {resp.status_code}]")
                except Exception as e:
                    results.append(f"[Exception: {str(e)}]")
                    
        return results
