import asyncio
import os
from dotenv import load_dotenv
import httpx
import json

async def test_draft():
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"Loaded GEMINI_API_KEY: {gemini_key[:10]}...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": "Return a JSON object with subject and email_body testing."}]}
        ],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }
    
    async with httpx.AsyncClient() as client:
        print("Calling Gemini API...")
        resp = await client.post(url, json=payload, timeout=10.0)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! Gemini works.")
            print(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
        else:
            print("Error:", resp.text)

if __name__ == "__main__":
    asyncio.run(test_draft())
