import asyncio
import traceback
from app.db.session import AsyncSessionLocal
from app.api.outreach import get_analytics

async def test():
    async with AsyncSessionLocal() as db:
        try:
            res = await get_analytics(campaign_id=None, db=db)
            print("SUCCESS analytics:", res)
        except Exception as e:
            print("ERROR IN ANALYTICS:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
