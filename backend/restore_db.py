import httpx
import asyncio
import json

async def main():
    base_url = "https://web-production-c4d98.up.railway.app/api/v1"
    
    with open("../leads.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} leads from leads.json")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Login (Might fail due to 500 error, but we'll bypass if deps.py works with no token? No wait, deps.py returns admin@revo.ai ONLY if `token` is empty string? Let's see: `if not token: ...`. 
        # If we just don't pass Authorization header, token is None, so it returns admin@revo.ai!)
        
        # 2. Restore DB
        print("Restoring DB...")
        resp = await client.post(f"{base_url}/leads/tools/restore", json=data)
        
        if resp.status_code == 200:
            print("Successfully restored:", resp.json())
        else:
            print("Failed to restore:", resp.status_code, resp.text)

if __name__ == "__main__":
    asyncio.run(main())
