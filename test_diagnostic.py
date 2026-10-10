import asyncio
import os
import sys

from sqlalchemy import select, String, cast

# Mock env for testing
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/apify_outreach"

async def test_stuck_leads():
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.lead import Lead
        from app.workers.enrichment_tasks import AIEnrichmentService
        import re
        from app.models.contact import Contact
        from app.services.messenger_checker import verify_messenger_availability

        print("Testing DB Connection...")
        async with AsyncSessionLocal() as db:
            print("Connected. Fetching stuck leads...")
            res = await db.execute(select(Lead).where(Lead.enrichment_status == "in_progress"))
            leads = res.scalars().all()
            print(f"Found {len(leads)} stuck leads")
            
            if not leads:
                print("No stuck leads. Testing Elephant Thai Spa Salon directly...")
                res = await db.execute(select(Lead).where(Lead.company_name.ilike('%Elephant Thai%')))
                leads = [res.scalars().first()]
                
            lead = leads[0]
            print(f"Testing Lead: {lead.company_name} | {lead.website}")
            
            # Step 1: Text extraction
            print("Step 1: Extracting text...")
            text, err_msg = await AIEnrichmentService.extract_website_text(lead.website)
            if not text:
                print(f"Failed extraction: {err_msg}")
            else:
                print(f"Success extraction. Length: {len(text)}")
                
                # Step 2: Gemini / Heuristic
                print("Step 2: Heuristic enrichment...")
                custom_vars = [
                    {"key": "has_online_booking", "description": "Does the site have online booking or appointment scheduling?"},
                    {"key": "uses_crm_chat", "description": "Does the site use WhatsApp or Live Chat widget?"}
                ]
                extracted_results = await AIEnrichmentService.batch_enrich_sites([{"lead_id": str(lead.id), "website": lead.website, "text": text}], custom_vars)
                print(f"Results: {extracted_results}")
                
                # Step 3: Messenger Check
                print("Step 3: Messenger check...")
                phone_to_check = lead.phone
                if not phone_to_check:
                    c_res = await db.execute(select(Contact).where(Contact.lead_id == lead.id, Contact.contact_type == "phone"))
                    first_phone = c_res.scalars().first()
                    if first_phone:
                        phone_to_check = first_phone.contact_value
                
                if phone_to_check:
                    print(f"Checking phone {phone_to_check}...")
                    info = await asyncio.to_thread(verify_messenger_availability, phone_to_check)
                    print(f"Messenger info: {info}")
                
                # Step 4: Regex
                print("Step 4: Regex extraction...")
                emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text))
                print(f"Emails found: {emails}")
                wa_links = set(re.findall(r'wa\.me/([0-9]+)', text))
                print(f"WA Links: {wa_links}")
                
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stuck_leads())
