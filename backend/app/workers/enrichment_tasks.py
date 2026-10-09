import asyncio
import logging
from typing import List
from celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.services.ai_enrichment import AIEnrichmentService
from sqlalchemy import select

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.workers.enrichment_tasks.run_campaign_enrichment")
def run_campaign_enrichment(self, campaign_id: str):
    """
    Celery task to scrape lead websites, find contacts & custom LLM variables.
    """
    logger.info(f"Starting enrichment task for campaign_id={campaign_id}")

    async def _process():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalars().first()
            if not campaign:
                return

            ai_cfg = campaign.ai_config or {}
            custom_vars = ai_cfg.get("custom_variables", [])

            # Get leads in campaign with a website
            leads_res = await db.execute(select(Lead).where(Lead.campaign_id == campaign_id, Lead.website.isnot(None)))
            leads = leads_res.scalars().all()

            if not leads:
                logger.info("No leads with websites found for enrichment.")
                return

            site_batches = []
            for lead in leads:
                text = await AIEnrichmentService.extract_website_text(lead.website)
                if text:
                    site_batches.append({
                        "lead_id": str(lead.id),
                        "website": lead.website,
                        "text": text
                    })

            # Process in batches of 5
            batch_size = 5
            for i in range(0, len(site_batches), batch_size):
                chunk = site_batches[i:i + batch_size]
                extracted_results = await AIEnrichmentService.batch_enrich_sites(chunk, custom_vars)
                
                for item in chunk:
                    lead_id = item["lead_id"]
                    if lead_id in extracted_results:
                        l_res = await db.execute(select(Lead).where(Lead.id == lead_id))
                        target_lead = l_res.scalars().first()
                        if target_lead:
                            existing_custom = dict(target_lead.custom_data) if target_lead.custom_data else {}
                            existing_custom.update(extracted_results[lead_id])
                            target_lead.custom_data = existing_custom
                            from sqlalchemy.orm.attributes import flag_modified
                            flag_modified(target_lead, "custom_data")
                
                await db.commit()
            logger.info(f"Enrichment completed for campaign {campaign_id}")

    asyncio.run(_process())

@celery_app.task(bind=True, name="app.workers.enrichment_tasks.run_targeted_enrichment")
def run_targeted_enrichment(self, lead_ids: List[str], custom_vars: List[dict] = None):
    logger.info(f"Starting targeted enrichment for {len(lead_ids)} leads")
    if not custom_vars:
        custom_vars = [
            {"key": "has_online_booking", "description": "Does the site have online booking or appointment scheduling?"},
            {"key": "uses_crm_chat", "description": "Does the site use WhatsApp or Live Chat widget?"}
        ]
        
    async def _process():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import cast, String
            leads_res = await db.execute(select(Lead).where(cast(Lead.id, String).in_(lead_ids), Lead.website.isnot(None)))
            leads = leads_res.scalars().all()
            if not leads:
                return

            site_batches = []
            for lead in leads:
                text = await AIEnrichmentService.extract_website_text(lead.website)
                if text:
                    site_batches.append({
                        "lead_id": str(lead.id),
                        "website": lead.website,
                        "text": text
                    })
                else:
                    # Mark as failed if no text could be extracted
                    existing_custom = dict(lead.custom_data) if lead.custom_data else {}
                    existing_custom["enrichment_status"] = "failed"
                    lead.custom_data = existing_custom
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(lead, "custom_data")
            await db.commit()

            batch_size = 5
            for i in range(0, len(site_batches), batch_size):
                chunk = site_batches[i:i + batch_size]
                extracted_results = await AIEnrichmentService.batch_enrich_sites(chunk, custom_vars)
                
                import re
                from app.models.contact import Contact
                for item in chunk:
                    lead_id = item["lead_id"]
                    l_res = await db.execute(select(Lead).where(cast(Lead.id, String) == lead_id))
                    target_lead = l_res.scalars().first()
                    if not target_lead: continue
                    
                    # Store AI custom data and mark completed
                    existing_custom = dict(target_lead.custom_data) if target_lead.custom_data else {}
                    if lead_id in extracted_results:
                        existing_custom.update(extracted_results[lead_id])
                    existing_custom["enrichment_status"] = "completed"
                    target_lead.custom_data = existing_custom
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(target_lead, "custom_data")
                        
                    # Extract Emails via Regex
                    emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', item["text"]))
                    for email in emails:
                        if len(email) < 50:
                            existing = await db.execute(select(Contact).where(Contact.lead_id == target_lead.id, Contact.contact_value == email))
                            if not existing.scalars().first():
                                db.add(Contact(lead_id=target_lead.id, contact_type="email", contact_value=email))
                                
                    # Extract wa.me links
                    wa_links = set(re.findall(r'wa\.me/([0-9]+)', item["text"]))
                    for wa in wa_links:
                        existing = await db.execute(select(Contact).where(Contact.lead_id == target_lead.id, Contact.contact_value == wa))
                        if not existing.scalars().first():
                            db.add(Contact(lead_id=target_lead.id, contact_type="whatsapp", contact_value=wa))
                    
                await db.commit()
            logger.info("Targeted enrichment completed")

    asyncio.run(_process())
