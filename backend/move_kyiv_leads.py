import asyncio
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.lead import Lead

async def move_leads():
    async with AsyncSessionLocal() as db:
        # Check if Campaign "Beauty Kyiv" exists
        result = await db.execute(select(Campaign).where(Campaign.campaign_name == "Beauty Kyiv"))
        kyiv_camp = result.scalars().first()
        
        if not kyiv_camp:
            print("Creating Beauty Kyiv campaign...")
            kyiv_camp = Campaign(
                campaign_name="Beauty Kyiv",
                status="PENDING",
                ai_config={
                    "custom_variables": [
                        {"key": "has_online_booking", "description": "Does the site have online booking?"},
                        {"key": "uses_crm_chat", "description": "Does the site use WhatsApp or Live Chat widget?"}
                    ]
                }
            )
            db.add(kyiv_camp)
            await db.commit()
            await db.refresh(kyiv_camp)
            
        print(f"Beauty Kyiv Campaign ID: {kyiv_camp.id}")
        
        # Move leads where city is 'Kyiv'
        # The database seems to have both 'Kyiv' and 'Київ'
        stmt = update(Lead).where(
            Lead.city.ilike("%Kyiv%") | Lead.address.ilike("%Kyiv%") | Lead.address.ilike("%Київ%")
        ).values(campaign_id=kyiv_camp.id)
        
        res = await db.execute(stmt)
        await db.commit()
        
        print(f"Successfully moved {res.rowcount} leads to Beauty Kyiv project!")

if __name__ == "__main__":
    asyncio.run(move_leads())
