import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.lead import Lead
from app.models.contact import Contact

async def test():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Lead).where(Lead.company_name.ilike('%Elephant%')))
        lead = res.scalars().first()
        if lead:
            print("Found lead:", lead.company_name, "Phone:", lead.phone)
            c_res = await db.execute(select(Contact).where(Contact.lead_id == lead.id, Contact.contact_type == 'phone'))
            contact = c_res.scalars().first()
            if contact:
                print("First contact:", contact.contact_value)
            else:
                print("No contacts found.")

asyncio.run(test())
