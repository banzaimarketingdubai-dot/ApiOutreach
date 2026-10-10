import asyncio
import httpx
from app.services.vault_helper import get_api_key

async def test():
    key = await get_api_key("gemini")
    print("Gemini key:", key)
    
if __name__ == "__main__":
    asyncio.run(test())
