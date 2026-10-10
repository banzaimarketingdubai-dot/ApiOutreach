import asyncio
import httpx
from app.services.vault_helper import get_api_key

async def test_gemini():
    gemini_key = await get_api_key("gemini")
    print("Got key:", gemini_key[:10] + "...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hello, say hi!"}]}]
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            print(resp.status_code)
            print(resp.text)
    except Exception as e:
        print("Error:", type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(test_gemini())
