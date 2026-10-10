import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.lead import Lead

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Lead).where(Lead.enrichment_status == 'in_progress'))
        leads = res.scalars().all()
        print(f"Found {len(leads)} stuck leads.")
        for i, l in enumerate(leads[:5]):
            print(f"Stuck Lead {i+1}: {l.company_name} | {l.website}")

        res2 = await db.execute(select(Lead).where(Lead.enrichment_status == 'failed'))
        failed = res2.scalars().all()
        print(f"Found {len(failed)} failed leads.")
        for i, l in enumerate(failed[:5]):
            print(f"Failed Lead {i+1}: {l.company_name} | custom_data: {l.custom_data.get('ai_logs', []) if l.custom_data else 'None'}")

asyncio.run(check())
