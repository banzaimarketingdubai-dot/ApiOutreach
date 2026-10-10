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

            # Process in batches of 25 to fully utilize Gemini's 1M token context window and reduce API RPM usage
            batch_size = 25
            for i in range(0, len(leads), batch_size):
                chunk_leads = leads[i:i + batch_size]
                site_batches = []
                
                # Extract text for this small batch concurrently
                import asyncio
                
                async def _extract_for_lead(l):
                    t, err = await AIEnrichmentService.extract_website_text(l.website)
                    return l, t, err
                    
                extraction_results = await asyncio.gather(*[_extract_for_lead(l) for l in chunk_leads])
                
                for lead, text, err_msg in extraction_results:
                    if text:
                        site_batches.append({
                            "lead_id": str(lead.id),
                            "website": lead.website,
                            "text": text
                        })
                    else:
                        existing_custom = dict(lead.custom_data) if lead.custom_data else {}
                        existing_custom["enrichment_status"] = "failed"
                        existing_custom["ai_logs"] = [f"[ERROR] {err_msg}"]
                        lead.custom_data = existing_custom
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(lead, "custom_data")
                
                await db.commit()

                if not site_batches:
                    continue

                # Enrich this batch
                extracted_results = await AIEnrichmentService.batch_enrich_sites(site_batches, custom_vars)
                
                import re
                from app.models.contact import Contact
                from app.services.messenger_checker import verify_messenger_availability
                for item in site_batches:
                    lead_id = item["lead_id"]
                    try:
                        l_res = await db.execute(select(Lead).where(cast(Lead.id, String) == lead_id))
                        target_lead = l_res.scalars().first()
                        if not target_lead: continue
                        
                        # Store AI custom data and mark completed
                        existing_custom = dict(target_lead.custom_data) if target_lead.custom_data else {}
                        if lead_id in extracted_results and extracted_results[lead_id]:
                            existing_custom.update(extracted_results[lead_id])
                            if "ai_logs" not in existing_custom:
                                existing_custom["ai_logs"] = []
                            existing_custom["ai_logs"].append(f"[SUCCESS] Analyzed {target_lead.website} and extracted custom variables.")
                        else:
                            if "ai_logs" not in existing_custom:
                                existing_custom["ai_logs"] = []
                            existing_custom["ai_logs"].append(f"[WARNING] API Rate limit or parse failure for this batch.")
                            
                        existing_custom["enrichment_status"] = "completed"
                        
                        # Auto-Check Messengers during enrichment
                        phone_to_check = target_lead.phone
                        if not phone_to_check:
                            c_res = await db.execute(select(Contact).where(Contact.lead_id == target_lead.id, Contact.contact_type == "phone"))
                            first_phone = c_res.scalars().first()
                            if first_phone:
                                phone_to_check = first_phone.contact_value

                        async def _check_msg(phone, custom_data_dict, lead_id):
                            try:
                                import asyncio
                                info = await asyncio.to_thread(verify_messenger_availability, phone)
                                custom_data_dict["telegram_available"] = info.get("telegram_available", False)
                                custom_data_dict["whatsapp_available"] = info.get("whatsapp_available", False)
                                custom_data_dict["viber_available"] = info.get("viber_available", False)
                                if "ai_logs" not in custom_data_dict:
                                    custom_data_dict["ai_logs"] = []
                                custom_data_dict["ai_logs"].append(f"[SUCCESS] Auto-checked messengers for {phone}")
                                
                                # Add to Contact table so UI shows icons
                                if custom_data_dict["whatsapp_available"]:
                                    existing = await db.execute(select(Contact).where(Contact.lead_id == lead_id, Contact.contact_type == "whatsapp"))
                                    if not existing.scalars().first():
                                        db.add(Contact(lead_id=lead_id, contact_type="whatsapp", contact_value=info.get("clean_phone", phone)))
                                if custom_data_dict["telegram_available"]:
                                    existing = await db.execute(select(Contact).where(Contact.lead_id == lead_id, Contact.contact_type == "telegram"))
                                    if not existing.scalars().first():
                                        db.add(Contact(lead_id=lead_id, contact_type="telegram", contact_value=info.get("clean_phone", phone)))
                            except Exception as e:
                                logger.error(f"Messenger check failed for {phone}: {e}")

                        if phone_to_check:
                            await _check_msg(phone_to_check, existing_custom, target_lead.id)
                                
                        target_lead.custom_data = existing_custom
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(target_lead, "custom_data")
                            
                        # Extract Emails via Regex
                        clean_text = item["text"].replace('\x00', '')
                        emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', clean_text))
                        for email in emails:
                            if len(email) < 50:
                                existing = await db.execute(select(Contact).where(Contact.lead_id == target_lead.id, Contact.contact_value == email))
                                if not existing.scalars().first():
                                    db.add(Contact(lead_id=target_lead.id, contact_type="email", contact_value=email))
                                    
                        # Extract wa.me links
                        wa_links = set(re.findall(r'wa\.me/([0-9]+)', clean_text))
                        for wa in wa_links:
                            existing = await db.execute(select(Contact).where(Contact.lead_id == target_lead.id, Contact.contact_value == wa))
                            if not existing.scalars().first():
                                db.add(Contact(lead_id=target_lead.id, contact_type="whatsapp", contact_value=wa))
                                
                        # Extract t.me links
                        tg_links = set(re.findall(r't\.me/([a-zA-Z0-9_]+)', clean_text))
                        for tg in tg_links:
                            existing = await db.execute(select(Contact).where(Contact.lead_id == target_lead.id, Contact.contact_value == tg))
                            if not existing.scalars().first():
                                db.add(Contact(lead_id=target_lead.id, contact_type="telegram", contact_value=tg))
                    except Exception as e:
                        logger.error(f"Fatal error processing lead {lead_id}: {e}")
                        try:
                            # Try to mark it as failed so it doesn't stay in_progress
                            l_res_err = await db.execute(select(Lead).where(cast(Lead.id, String) == lead_id))
                            err_lead = l_res_err.scalars().first()
                            if err_lead:
                                err_custom = dict(err_lead.custom_data) if err_lead.custom_data else {}
                                err_custom["enrichment_status"] = "failed"
                                if "ai_logs" not in err_custom:
                                    err_custom["ai_logs"] = []
                                err_custom["ai_logs"].append(f"[ERROR] Internal server error during processing: {str(e)}")
                                err_lead.custom_data = err_custom
                                flag_modified(err_lead, "custom_data")
                        except Exception:
                            pass
                    
                await db.commit()
                # Cooldown to respect Gemini 15 RPM limits
                await asyncio.sleep(5)
                
            logger.info("Targeted enrichment completed")

    asyncio.run(_process())
