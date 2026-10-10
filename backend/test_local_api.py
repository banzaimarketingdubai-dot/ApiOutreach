import asyncio
import traceback
from app.db.session import AsyncSessionLocal
from app.api.leads import list_leads

async def test_leads():
    async with AsyncSessionLocal() as db:
        try:
            res = await list_leads(db=db, page=1, page_size=10)
            print("SUCCESS! Leads count:", len(res["items"]))
        except Exception as e:
            print("ERROR:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_leads())
