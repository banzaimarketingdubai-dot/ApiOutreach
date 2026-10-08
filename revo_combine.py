"""
revo_combine.py — Revo B2B Google Maps Lead Generation Combine Pipeline
=======================================================================
Единый конвейер поиска, квалификации, графического аудита и рассылки лидов под услугу Revo.

Этапы:
  1. Первичный парсинг Google Карт (scraper.py) по целевым категориям (КаБаРе, барбершопы, клиники, салоны красоты, груминг).
  2. Авто-обогащение лидов: поиск Email и контактов на сайтах клиентов.
  3. Расчет баллов Revo Score (0-100%) и точек роста (revo_audit_engine.py).
  4. Генерация HD PNG графической карточки аудита (revo_visual_renderer.py).
  5. Отправка персонализированных HTML-писем с inline-графикой и антиспам-защитой (revo_email_dispatcher.py).
  6. Экспорт в Google Таблицу (upload_to_sheets.py) со всеми 13 колонками.

Запуск:
    python revo_combine.py
"""

import os
import sys
import time
import random
import logging
import argparse
from dotenv import load_dotenv

from scraper import run_scraper, save_leads, SEARCH_QUERIES, OUTPUT_FILE
from upload_to_sheets import upload_to_sheets
from outreach_combine import scrape_email_from_website
from revo_visual_renderer import generate_revo_audit_image
from revo_email_dispatcher import send_revo_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("RevoCombine")


def run_revo_pipeline(
    queries: list[str] = None,
    max_places: int = None,
    skip_enrichment: bool = False,
    send_emails: bool = False,
    geo: str = None
):
    load_dotenv()
    log.info("=" * 65)
    log.info("🚀 СТАРТ REVO B2B LEAD GENERATION COMBINE")
    if geo:
        log.info(f"📍 Target GEO: {geo}")
    log.info("=" * 65)

    # ── ШАГ 0: Сброс локального буфера лидов перед новым сбором ──────────────
    save_leads([], OUTPUT_FILE)

    # ── ШАГ 1: Первичный парсинг Google Maps ────────────────────────────────
    log.info("📌 ШАГ 1: Первичный парсинг Google Карт...")
    leads = run_scraper(queries=queries, max_places=max_places)

    if not leads:
        log.warning("⚠️  Лиды не найдены. Завершение работы.")
        return

    log.info(f"✅ Найдено {len(leads)} релевантных бизнесов в целевых категориях.")

    # ── ШАГ 2 & 3 & 4: Обогащение + Аудит + Графическая карточка ──────────────
    log.info("\n📌 ШАГ 2 & 3: Обогащение контактов, расчет Revo Score и графический аудит...")
    enriched_count = 0
    generated_cards = 0

    for idx, lead in enumerate(leads, start=1):
        company = lead.get("company_name", "Unknown")
        website = lead.get("website", "")
        current_email = lead.get("email", "")

        log.info(f"\n[{idx}/{len(leads)}] Обработка компании: «{company}»...")

        # Поиск email
        if website and not current_email and not skip_enrichment:
            scraped_email = scrape_email_from_website(website)
            if scraped_email:
                lead["email"] = scraped_email
                enriched_count += 1

        # Генерация графической карточки аудита через Playwright
        img_path, audit_data = generate_revo_audit_image(lead)
        if img_path:
            generated_cards += 1
            lead["screenshot_path"] = str(img_path)

        # Обновление данных лида результатами аудита
        lead["revo_score"] = audit_data["overall_score"]
        lead["revo_potential"] = audit_data["potential_loss_pct"]
        lead["revo_audit_note"] = audit_data["status_label"] + ": " + "; ".join(audit_data["bottlenecks"])

        # ── ШАГ 5: Отправка имейлов (если включено) ─────────────────────────
        target_email = lead.get("email", "")
        if send_emails and target_email:
            from email_queue_manager import can_send_email_now, record_email_sent, queue_lead_for_later

            can_send, reason, remaining_hours = can_send_email_now(target_email)
            if can_send:
                log.info(f"   ✉️  Отправка персонализированного имейла на {target_email}...")
                ok, err = send_revo_email(target_email, audit_data, img_path)
                if ok:
                    lead["status"] = "Отправлено"
                    record_email_sent(target_email, company)
                else:
                    lead["status"] = f"Ошибка: {err[:30]}"

                # Антиспам задержка между письмами (60 - 180 сек)
                if idx < len(leads):
                    sleep_sec = random.randint(60, 180)
                    log.info(f"   ⏳ Пауза Anti-Spam: {sleep_sec} сек...")
                    time.sleep(sleep_sec)
            else:
                scheduled_str = queue_lead_for_later(lead, audit_data, img_path)
                lead["status"] = f"В очереди ({scheduled_str})"
                log.info(f"   🛡️  Защита от спама: {reason}. Поставлено в очередь на {scheduled_str}")
        else:
            lead["status"] = "Готов к рассылке"

    # Сохраняем обновленные лиды
    save_leads(leads, OUTPUT_FILE)
    log.info(f"✅ Обработано {len(leads)} лидов. Создано графических аудитов: {generated_cards}")

    # ── ШАГ 6: Экспорт в Google Sheets ──────────────────────────────────────
    log.info("\n📌 ШАГ 6: Экспорт результатов в Google Таблицу...")
    try:
        upload_to_sheets(filepath=OUTPUT_FILE, geo=geo)
        log.info(f"✅ Успешно выгружено в Google Sheets (лист: Revo_{geo if geo else 'Leads'})!")
    except Exception as e:
        log.error(f"❌ Ошибка выгрузки в Google Sheets: {e}")

    log.info("=" * 65)
    log.info("🎉 РАБОТА КОМБАЙНА REVO УСПЕШНО ЗАВЕРШЕНА")
    log.info("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Revo B2B Lead Generation Combine")
    parser.add_argument("--limit", type=int, help="Максимальное количество мест на поисковый запрос", default=None)
    parser.add_argument("--skip-enrichment", action="store_true", help="Пропустить этап парсинга email с сайтов")
    parser.add_argument("--send-emails", action="store_true", help="Включить реальную отправку писем клиентам")
    args = parser.parse_args()

    try:
        run_revo_pipeline(
            max_places=args.limit,
            skip_enrichment=args.skip_enrichment,
            send_emails=args.send_emails
        )
    except Exception as e:
        log.error(f"❌ Фатальная ошибка комбайна: {e}", exc_info=True)
        sys.exit(1)
