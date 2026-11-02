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
            campaign.error_log = None
            await db.commit()

            async def add_log(level: str, msg: str):
                log_entry = {"level": level, "message": msg, "timestamp": datetime.utcnow().isoformat() + "Z"}
                new_logs = list(campaign.logs) if campaign.logs else []
                new_logs.append(log_entry)
                campaign.logs = new_logs
                await db.commit()

            async def fail_campaign(error_message: str):
                logger.error(f"[Scraping Failed] Campaign {campaign_id}: {error_message}")
                campaign.status = CampaignStatus.FAILED
                campaign.error_log = error_message
                curr_stats = dict(campaign.stats or {})
                curr_stats["errors"] = (curr_stats.get("errors") or 0) + 1
                campaign.stats = curr_stats
                await add_log("error", f"Ошибка сбора: {error_message}")
                
                # Propagate error to linked audience
                if campaign.audience_id:
                    try:
                        from app.models.audience import Audience
                        aud_res = await db.execute(select(Audience).where(Audience.id == campaign.audience_id))
                        target_aud = aud_res.scalars().first()
                        if target_aud:
                            aud_stats = dict(target_aud.stats or {})
                            aud_stats["last_error"] = error_message
                            aud_stats["status"] = "FAILED"
                            target_aud.stats = aud_stats
                            await db.commit()
                    except Exception as aud_err:
                        logger.warning(f"Failed to record audience error: {aud_err}")
                await db.commit()

            try:
                ai_cfg = campaign.ai_config or {}
                queries = ai_cfg.get("search_queries", [f"Dental Clinic in {campaign.target_geo or 'Dubai'}"])
                max_places = ai_cfg.get("max_places", 50)
                await add_log("info", f"Запущен сбор данных для {len(queries)} поисковых запросов (макс. {max_places} мест).")

                from app.services.vault_helper import get_api_key
                api_token = await get_api_key("apify")
                if not api_token:
                    await fail_campaign("API токен Apify не настроен в Vault (раздел Настройки). Укажите рабочий токен Apify для запуска парсера.")
                    return

                # Budget Guard Check
                try:
                    from app.api.apify import get_apify_balance
                    balance_data = await get_apify_balance()
                    rem_usd = balance_data.get("remaining_usd", 1.0)
                    if balance_data.get("connected") and rem_usd < 0.5:
                        await fail_campaign(f"Budget Guard: Недостаточный баланс Apify (${rem_usd:.2f} < $0.50). Пополните баланс на apify.com для продолжения.")
                        return
                except Exception as b_err:
                    logger.warning(f"Could not check Apify balance: {b_err}")

                scraped_items = []
                if campaign.status == CampaignStatus.CANCELLED:
                    await add_log("warning", "Сбор данных прерван: кампания была остановлена оператором.")
                    return

                try:
                    client = ApifyClient(api_token)
                    run_input = {
                        "searchStringsArray": queries,
                        "maxCrawledPlaces": max_places,
                        "language": "en"
                    }
                    await add_log("info", f"Вызов Apify Actor '{ACTOR_ID}' по запросам: {', '.join(queries[:3])}...")
                    run_res = client.actor(ACTOR_ID).call(run_input=run_input)
                    dataset_id = run_res.get("defaultDatasetId") if isinstance(run_res, dict) else getattr(run_res, "default_dataset_id", None)
                    if not dataset_id:
                        await fail_campaign(f"Apify Actor завершился без создания датасета. Ответ сервиса: {run_res}")
                        return

                    await add_log("info", f"Apify Actor успешно отработал. Dataset ID: {dataset_id}")
                    for item in client.dataset(dataset_id).iterate_items():
                        scraped_items.append(item)
                    await add_log("success", f"Загружено {len(scraped_items)} сырых записей из Apify.")
                except Exception as apify_err:
                    logger.error(f"Apify call failed: {apify_err}")
                    await fail_campaign(f"Ошибка Apify API: {str(apify_err)}")
                    return

                if not scraped_items:
                    await fail_campaign(f"Apify не нашел результатов по запросам: {', '.join(queries[:3])}. Проверьте геолокацию и ключевые слова.")
                    return

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
                        await add_log("error", "Задача прервана: кампания остановлена оператором.")
                        return

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

                    lead_obj, is_new = await merger.merge_or_create_lead(
                        lead_data,
                        campaign_id=campaign.id,
                        project_id=campaign.project_id,
                        audience_id=campaign.audience_id
                    )
                    if is_new:
                        saved_count += 1
                    else:
                        merged_count += 1

                campaign.stats = {
                    "total_scraped": len(scraped_items),
                    "new_leads_created": saved_count,
                    "merged_leads": merged_count,
                    "errors": 0
                }
                campaign.status = CampaignStatus.COMPLETED
                campaign.error_log = None
                await add_log("success", f"Сбор контактов завершен! Добавлено {saved_count} новых лидов, смерджено {merged_count}.")
                await db.commit()

                # Refresh audience stats if linked to an audience
                if campaign.audience_id:
                    try:
                        from app.api.audiences import compute_audience_stats
                        from app.models.audience import Audience
                        aud_stats = await compute_audience_stats(db, campaign.audience_id)
                        aud_res = await db.execute(select(Audience).where(Audience.id == campaign.audience_id))
                        target_aud = aud_res.scalars().first()
                        if target_aud:
                            aud_dict = dict(aud_stats)
                            aud_dict.pop("last_error", None)
                            aud_dict["status"] = "COMPLETED"
                            target_aud.stats = aud_dict
                            await db.commit()
                    except Exception as aud_stat_err:
                        logger.warning(f"Failed to refresh audience stats: {aud_stat_err}")
                await db.commit()

                # Trigger Enrichment task for leads with website
                if campaign.status != CampaignStatus.CANCELLED:
                    from app.workers.enrichment_tasks import run_campaign_enrichment
                    run_campaign_enrichment.delay(campaign_id)

            except Exception as unhandled_err:
                logger.exception(f"Unhandled error in campaign scraping {campaign_id}: {unhandled_err}")
                await fail_campaign(f"Системный сбой конвейера парсинга: {str(unhandled_err)}")

    asyncio.run(_process())
