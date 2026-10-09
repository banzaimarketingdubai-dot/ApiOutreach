import httpx
import asyncio

async def main():
    base_url = "https://web-production-c4d98.up.railway.app/api/v1"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Create Campaign
        print("Creating Campaign...")
        campaign_data = {
            "campaign_name": "Beauty Kyiv",
            "target_niche": "Beauty & SPA",
            "target_location": "Kyiv, Ukraine",
            "daily_lead_goal": 50,
            "apify_max_items": 1000,
            "ai_config": {
                "campaign_name": "Beauty Kyiv",
                "target_geo": "Kyiv, Ukraine",
                "target_niches": ["Beauty", "SPA"],
                "search_queries": ["SPA Kyiv"],
                "custom_variables": []
            }
        }
        resp = await client.post(f"{base_url}/campaigns", json=campaign_data)
        if resp.status_code != 201:
            print("Failed to create campaign:", resp.status_code, resp.text)
            return
            
        campaign = resp.json()
        campaign_id = campaign["id"]
        print(f"Created Campaign '{campaign['name']}' with ID: {campaign_id}")
        
        # 2. Assign Leads
        print("Assigning all unassigned leads to this campaign...")
        assign_resp = await client.post(f"{base_url}/leads/tools/assign_all", json={"campaign_id": campaign_id})
        
        if assign_resp.status_code == 200:
            print("Successfully assigned leads:", assign_resp.json())
        else:
            print("Failed to assign:", assign_resp.status_code, assign_resp.text)

if __name__ == "__main__":
    asyncio.run(main())
