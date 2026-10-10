import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        res = await client.get('https://web-production-c4d98.up.railway.app/api/v1/outreach/debug_models', timeout=30.0)
        print("Status:", res.status_code)
        try:
            data = res.json()
            models = data.get('models', [])
            if not models:
                print(data)
            for m in models:
                if 'flash' in m.get('name', '').lower() or 'gemini' in m.get('name', '').lower():
                    print(m.get('name'))
        except Exception as e:
            print("Response text:", res.text)

if __name__ == "__main__":
    asyncio.run(test())
