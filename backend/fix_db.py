import asyncio
import json
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.lead import Lead

async def fix_reviews_count():
    print("Loading leads.json...")
    try:
        with open('c:\\Sher_AI_Studio\\projects\\Apify Outreach\\leads.json', 'r', encoding='utf-8') as f:
            raw_leads = json.load(f)
    except Exception as e:
        print("Could not load leads.json:", e)
        return

    # Map company name to reviews_count
    company_to_reviews = {}
    for r in raw_leads:
        name = r.get("company_name")
        reviews = int(r.get("reviews_count") or r.get("reviewsCount") or r.get("reviews") or 0)
        rating = float(r.get("rating") or r.get("totalScore") or 0.0)
        if name and reviews > 0:
            company_to_reviews[name] = {"reviews": reviews, "rating": rating}

    print(f"Found {len(company_to_reviews)} leads with reviews in JSON.")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Lead))
        db_leads = res.scalars().all()
        
        updated = 0
        for lead in db_leads:
            if (lead.reviews_count == 0 or lead.reviews_count is None) and lead.company_name in company_to_reviews:
                lead.reviews_count = company_to_reviews[lead.company_name]["reviews"]
                if lead.rating == 0 or lead.rating is None:
                    lead.rating = company_to_reviews[lead.company_name]["rating"]
                updated += 1
        
        if updated > 0:
            await db.commit()
            print(f"Successfully fixed {updated} leads in the database!")
        else:
            print("No leads needed fixing.")

if __name__ == "__main__":
    asyncio.run(fix_reviews_count())
