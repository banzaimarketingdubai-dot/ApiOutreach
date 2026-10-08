import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.insert(0, r"c:\Sher_AI_Studio\projects\Apify Outreach\backend")

from app.db.session import SessionLocal
from app.models.campaign import Campaign, CampaignStatus
from sqlalchemy import select

async def main():
    async with SessionLocal() as db:
        campaign_id = "a9eee752-04b2-464c-864d-b53beedb8359"
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        res = await db.execute(stmt)
        c = res.scalars().first()
        
        if c:
            c.status = CampaignStatus.PAUSED
            
            from datetime import datetime
            log_entry = {"level": "warning", "message": "Campaign paused by operator.", "timestamp": datetime.utcnow().isoformat() + "Z"}
            new_logs = list(c.logs) if c.logs else []
            new_logs.append(log_entry)
            c.logs = new_logs
            
            await db.commit()
            print("Successfully updated campaign!")
        else:
            print("Campaign not found")

if __name__ == "__main__":
    asyncio.run(main())
