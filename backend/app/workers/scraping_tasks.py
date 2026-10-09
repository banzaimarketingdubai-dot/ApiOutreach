import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from apify_client import ApifyClient
from celery_app import celery_app
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.campaign import Campaign, CampaignStatus
from app.services.entity_resolution import LeadMergerService, normalize_phone
from app.services.scoring import calculate_revo_score_and_audit
from sqlalchemy import select

logger = logging.getLogger(__name__)

ACTOR_ID = "compass/google-maps-extractor"

@celery_app.task(bind=True, name="app.workers.scraping_tasks.run_campaign_scraping")
def run_campaign_scraping(self, campaign_id: str):
    """
    Celery task to run Apify Google Maps actor based on Campaign configuration.
    """
    logger.info(f"Starting campaign scraping task for campaign_id={campaign_id}")
    
    async def _process():
        async with AsyncSessionLocal() as db:
            # Fetch campaign
            result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = result.scalars().first()
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found.")
                return

            campaign.status = CampaignStatus.RUNNING
            await db.commit()

            async def add_log(level: str, msg: str):
                log_entry = {"level": level, "message": msg, "timestamp": datetime.utcnow().isoformat() + "Z"}
                new_logs = list(campaign.logs) if campaign.logs else []
                new_logs.append(log_entry)
                campaign.logs = new_logs
                await db.commit()

            ai_cfg = campaign.ai_config or {}
            await add_log("info", f"Started scraping for {len(ai_cfg.get('search_queries', []))} queries.")

            queries = ai_cfg.get("search_queries", [f"Dental Clinic in {campaign.target_geo or 'Dubai'}"])
            max_places = ai_cfg.get("max_places", 50)

            from app.services.vault_helper import get_api_key
            api_token = await get_api_key("apify")
            scraped_items = []

            if api_token:
                try:
                    # Budget Guard Check
                    from app.api.apify import get_apify_balance
                    balance_data = await get_apify_balance()
                    if balance_data.get("connected") and balance_data.get("remaining_usd", 1.0) < 0.5:
                        await add_log("error", f"Budget Guard: Apify balance too low (${balance_data.get('remaining_usd')}). Pausing campaign.")
                        campaign.status = CampaignStatus.PAUSED
                        await db.commit()
                        
                        # Wait for admin to resume
                        while campaign.status == CampaignStatus.PAUSED:
                            await asyncio.sleep(10)
                            await db.refresh(campaign)

                    if campaign.status != CampaignStatus.CANCELLED:
                        client = ApifyClient(api_token)
                        run_input = {
                            "searchStringsArray": queries,
                            "maxCrawledPlaces": max_places,
                            "language": "en"
                        }
                        run_res = client.actor(ACTOR_ID).call(run_input=run_input)
                        dataset_id = run_res.get("defaultDatasetId") if isinstance(run_res, dict) else getattr(run_res, "default_dataset_id", None)
                        if dataset_id:
                            await add_log("info", f"Apify Actor finished. Dataset ID: {dataset_id}")
                            for item in client.dataset(dataset_id).iterate_items():
                                scraped_items.append(item)
                            await add_log("success", f"Downloaded {len(scraped_items)} raw items from Apify.")
                    else:
                        await add_log("warning", "Scraping aborted because campaign was cancelled.")

                except Exception as e:
                    logger.error(f"Apify call failed: {e}")
                    campaign.error_log = f"Apify error: {str(e)}"
                    await add_log("error", f"Apify integration failed: {e}")

            if not scraped_items:
                logger.warning(f"Apify returned 0 items for campaign {campaign_id}.")
                await add_log("warning", f"Apify returned 0 items. No data scraped.")

            merger = LeadMergerService(db)
            saved_count = 0
            merged_count = 0

            for raw in scraped_items:
                # Check status periodically
                await db.refresh(campaign)
                while campaign.status == CampaignStatus.PAUSED:
                    await asyncio.sleep(3)
                    await db.refresh(campaign)
                
                if campaign.status == CampaignStatus.CANCELLED:
                    await add_log("error", "Task aborted: Campaign was cancelled.")
                    break
                title = raw.get("title") or raw.get("name")
                if not title:
                    continue

                phone = raw.get("phone") or raw.get("phoneUnformatted")
                website = raw.get("website")
                rating = float(raw.get("totalScore") or raw.get("rating") or 0.0)
                reviews = int(raw.get("reviewsCount") or raw.get("reviews") or 0)
                loc = raw.get("location") or {}
                lat = loc.get("lat") or raw.get("latitude")
                lng = loc.get("lng") or raw.get("longitude")

                has_phone = bool(phone)
                has_web = bool(website)
                
                # Fetch hot-swapped config dynamically
                current_ai_cfg = campaign.ai_config or {}

                score, audit_notes = calculate_revo_score_and_audit(
                    rating=rating,
                    reviews_count=reviews,
                    has_website=has_web,
                    has_phone=has_phone,
                    scoring_rules=current_ai_cfg.get("scoring_rules", {})
                )

                lead_data = {
                    "company_name": title,
                    "business_type": raw.get("categoryName") or "Business",
                    "city": campaign.target_geo,
                    "address": raw.get("address"),
                    "latitude": lat,
                    "longitude": lng,
                    "website": website,
                    "phone": phone,
                    "rating": rating,
                    "reviews_count": reviews,
                    "revo_score": score,
                    "audit_notes": audit_notes,
                    "source": "gmaps"
                }

                lead_obj, is_new = await merger.merge_or_create_lead(lead_data, campaign_id=campaign.id)
                if is_new:
                    saved_count += 1
                else:
                    merged_count += 1

            campaign.stats = {
                "total_scraped": len(scraped_items),
                "new_leads_created": saved_count,
                "merged_leads": merged_count
            }
            if campaign.status != CampaignStatus.CANCELLED:
                campaign.status = CampaignStatus.COMPLETED
                await add_log("success", f"Scraping completed. Added {saved_count} new leads, merged {merged_count}.")
            await db.commit()

            # Trigger Enrichment task for leads with website
            if campaign.status != CampaignStatus.CANCELLED:
                from app.workers.enrichment_tasks import run_campaign_enrichment
                run_campaign_enrichment.delay(campaign_id)

    asyncio.run(_process())
