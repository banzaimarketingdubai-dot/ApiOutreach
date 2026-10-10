import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Use a dummy UUID that won't exist just to see if we get a 404 or a 500
        # Actually, let's use the exact lead ID from the screenshot if possible, or any valid one.
        # But wait, without a valid lead ID we get 404. Let's fetch a lead first.
        res = await client.get('https://web-production-c4d98.up.railway.app/api/v1/leads?page_size=1')
        leads = res.json().get('items', [])
        if not leads:
            print("No leads found")
            return
            
        lead_id = leads[0]['id']
        print(f"Testing draft for lead {lead_id}")
        
        payload = {
            "lead_id": lead_id,
            "prompt": "Test prompt"
        }
        draft_res = await client.post('https://web-production-c4d98.up.railway.app/api/v1/outreach/draft', json=payload, timeout=60.0)
        
        print("Status:", draft_res.status_code)
        print("Response:", draft_res.text)

if __name__ == "__main__":
    asyncio.run(test())
