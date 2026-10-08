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
                            existing_custom = target_lead.custom_data or {}
                            existing_custom.update(extracted_results[lead_id])
                            target_lead.custom_data = existing_custom
                
                await db.commit()
            logger.info(f"Enrichment completed for campaign {campaign_id}")

    asyncio.run(_process())
