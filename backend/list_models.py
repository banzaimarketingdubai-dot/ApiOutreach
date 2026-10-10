import asyncio
import httpx
from app.services.vault_helper import get_api_key

async def list_models():
    gemini_key = await get_api_key("gemini")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        print(resp.status_code)
        import json
        models = resp.json().get('models', [])
        for m in models:
            if 'flash' in m.get('name', '').lower() or 'gemini' in m.get('name', '').lower():
                print(m.get('name'))

if __name__ == "__main__":
    asyncio.run(list_models())
