import asyncio
from app.db.session import AsyncSessionLocal
from app.models.lead import Lead
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Lead).where(Lead.custom_data['enrichment_status'].astext == 'failed').limit(5))
        leads = res.scalars().all()
        for l in leads:
            print(l.website, l.custom_data.get('ai_logs', []))

asyncio.run(run())
