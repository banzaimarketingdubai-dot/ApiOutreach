"""
scraper.py — Автоматический парсер B2B-лидов из Google Maps под услугу Revo
=======================================================================
Цель: Сбор бизнесов сферы обслуживания с моделью многократного возвращения
      клиентов (ретеншн: КаБаРе, барбершопы, клиники, салоны красоты, груминги),
      с имеющимся профилем на Google Картах, но с признаками слабой/неполной
      оптимизации (мало отзывов, низкий рейтинг, отсутствие сайта/фото).

Результат: файл leads.json со всеми атрибутами лида и оценкой Revo.
"""

import os
import re
import json
import logging
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from dotenv import load_dotenv
from apify_client import ApifyClient

# ─────────────────────────────────────────────
# 0. КОНФИГУРАЦИЯ ЛОГИРОВАНИЯ
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 1. ПАРАМЕТРЫ ЗАПУСКА REVO COMBINE
# ─────────────────────────────────────────────

# Actor на Apify Store (проверенный, официальный скрапер Google Maps)
ACTOR_ID = "compass/google-maps-extractor"

# Поисковые запросы под бизнесы с выстроенным ретеншн (КаБаРе, барбершопы, клиники, салоны красоты, груминги)
SEARCH_QUERIES = [
    "Barbershop Dubai",
    "Beauty Salon Dubai",
    "Dental Clinic Dubai",
    "Restaurant Dubai Marina",
    "Cafe Business Bay Dubai",
    "Pet Grooming Dubai",
    "Veterinary Clinic Dubai",
    "Spa & Wellness Center Dubai",
]

# Лимит мест на один запрос (для тестов 30-50, для полного сбора — 100-300)
MAX_CRAWLED_PLACES = int(os.getenv("MAX_CRAWLED_PLACES", "50"))

# Имя выходного файла
OUTPUT_FILE = "leads.json"

# UTM-параметры и трекинговые метки, которые нужно вырезать из URL
UTM_PARAMS_TO_STRIP = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "yclid", "_ga", "ref", "referrer",
}


# ─────────────────────────────────────────────
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ОЦЕНКА REVO
# ─────────────────────────────────────────────

def strip_utm(url: str) -> str:
    """
    Очищает URL от UTM-меток и трекинговых параметров.
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        clean_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in UTM_PARAMS_TO_STRIP
        }
        clean_query = urlencode(clean_params, doseq=True)
        clean_url = urlunparse(parsed._replace(query=clean_query))
        return clean_url
    except Exception:
        return url


def normalize_phone(raw_phone: str) -> str:
    """
    Приводит телефон к читаемому международному формату.
    """
    if not raw_phone:
        return ""

    digits_only = re.sub(r"[^\d+]", "", raw_phone)

    if digits_only.startswith("00971"):
        return "+" + digits_only[2:]
    elif digits_only.startswith("+971"):
        return digits_only
    elif digits_only.startswith("971"):
        return "+" + digits_only
    elif digits_only.startswith("0") and len(digits_only) >= 9:
        return "+971" + digits_only[1:]
    else:
        return raw_phone


def evaluate_revo_potential(rating: float, reviews_count: int, website: str, is_claimed: bool, photos_count: int) -> tuple[str, str]:
    """
    Вычисляет потенциал лида под услугу Revo (продвижение + сбор отзывов + лидогенерация).
    Возвращает (revo_potential, revo_audit_note).
    """
    reasons = []

    if not website:
        reasons.append("Нет собственного сайта в карточке")
    if reviews_count == 0:
        reasons.append("Нет отзывов (0)")
    elif reviews_count < 40:
        reasons.append(f"Мало отзывов ({reviews_count})")
    
    if 0 < rating < 4.4:
        reasons.append(f"Низкий рейтинг ({rating}★)")
    
    if not is_claimed:
        reasons.append("Профиль не подтвержден владельцем")

    if photos_count < 5:
        reasons.append("Мало фотографий в профиле")

    if not reasons:
        return "LOW", "Профиль хорошо заполнен и имеет высокий рейтинг"

    if len(reasons) >= 2 or reviews_count < 25 or (0 < rating < 4.3):
        potential = "HIGH"
    else:
        potential = "MEDIUM"

    audit_note = "; ".join(reasons)
    return potential, audit_note


def extract_lead(item: dict) -> dict | None:
    """
    Извлекает и нормализует данные одного результата из Apify-датасета Google Maps.
    Служит фильтром: карточка должна существовать и иметь контакты (телефон или сайт).
    """
    # ── Название компании ─────────────────────────────────────────────────
    company_name = (
        item.get("title")
        or item.get("name")
        or ""
    ).strip()

    if not company_name:
        return None

    # ── Тип бизнеса (Категория) ──────────────────────────────────────────
    category_raw = (
        item.get("categoryName")
        or (item.get("categories", ["N/A"])[0] if isinstance(item.get("categories"), list) and item.get("categories") else "N/A")
    )
    if isinstance(category_raw, list):
        business_type = ", ".join(category_raw)
    else:
        business_type = str(category_raw).strip()

    # ── Адрес ─────────────────────────────────────────────────────────────
    address = (
        item.get("address")
        or item.get("street")
        or item.get("city")
        or "N/A"
    ).strip()

    # ── Ссылка на Google Maps ─────────────────────────────────────────────
    google_maps_url = (
        item.get("url")
        or item.get("googleMapsUrl")
        or item.get("placeUrl")
        or ""
    ).strip()

    # ── Сайт ─────────────────────────────────────────────────────────────
    website_raw = (
        item.get("website")
        or ""
    ).strip()
    website = strip_utm(website_raw)

    # ── Телефон ───────────────────────────────────────────────────────────
    phone_raw = (
        item.get("phone")
        or item.get("phoneUnformatted")
        or item.get("internationalPhoneNumber")
        or ""
    ).strip()
    phone = normalize_phone(phone_raw)

    # Обязательное условие: у бизнеса должен быть хотя бы 1 контакт для связи (телефон или сайт)
    if not phone and not website:
        return None

    # ── Рейтинг и отзывы ──────────────────────────────────────────────────
    try:
        rating = float(item.get("totalScore") or item.get("rating") or item.get("stars") or 0.0)
    except (ValueError, TypeError):
        rating = 0.0

    try:
        reviews_count = int(item.get("reviewsCount") or item.get("reviews") or 0)
    except (ValueError, TypeError):
        reviews_count = 0

    photos_count = int(item.get("imageCount") or item.get("photosCount") or len(item.get("images", []) if isinstance(item.get("images"), list) else []))
    is_claimed = item.get("isClaimed", True)

    # Оценка потенциала Revo
    revo_potential, revo_audit_note = evaluate_revo_potential(rating, reviews_count, website, is_claimed, photos_count)

    return {
        "business_type":    business_type,
        "company_name":     company_name,
        "address":          address,
        "google_maps_url":  google_maps_url,
        "website":          website,
        "phone":            phone,
        "email":            item.get("email", ""), # Обогащается позже
        "rating":           rating,
        "reviews_count":    reviews_count,
        "revo_potential":   revo_potential,
        "revo_audit_note":  revo_audit_note,
    }


# ─────────────────────────────────────────────
# 3. ОСНОВНАЯ ЛОГИКА СРАПИНГА
# ─────────────────────────────────────────────

def run_scraper(queries: list[str] = None, max_places: int = None) -> list[dict]:
    """
    Запускает Apify Actor и возвращает отфильтрованный список лидов Revo.
    """
    load_dotenv()
    api_token = os.getenv("APIFY_API_TOKEN")

    if not api_token:
        raise EnvironmentError(
            "APIFY_API_TOKEN не найден. "
            "Добавь валидный APIFY_API_TOKEN в файл .env"
        )

    search_queries = queries or SEARCH_QUERIES
    limit_places = max_places or MAX_CRAWLED_PLACES

    log.info("✅ API-токен Apify загружен из .env")
    client = ApifyClient(api_token)

    run_input = {
        "searchStringsArray": search_queries,
        "maxCrawledPlaces": limit_places,
        "language": "en",
        "includeWebResults": False,
        "deeperCityScrape": False,
    }

    log.info(f"🚀 Запуск Apify Actor '{ACTOR_ID}' под задачу Revo...")
    log.info(f"   Поисковые запросы ({len(search_queries)}): {search_queries}")
    log.info(f"   Лимит на запрос: {limit_places}")

    run_result = client.actor(ACTOR_ID).call(run_input=run_input)

    if hasattr(run_result, "default_dataset_id"):
        dataset_id = run_result.default_dataset_id
    elif hasattr(run_result, "defaultDatasetId"):
        dataset_id = run_result.defaultDatasetId
    else:
        dataset_id = run_result.get("defaultDatasetId") if isinstance(run_result, dict) else None

    if not dataset_id:
        raise RuntimeError("Actor завершился без ID датасета.")

    log.info(f"✅ Actor завершён. Dataset ID: {dataset_id}")

    raw_count   = 0
    leads       = []
    skipped     = 0

    log.info("🔍 Фильтрация и оценка профилей Revo...")

    for item in client.dataset(dataset_id).iterate_items():
        raw_count += 1
        lead = extract_lead(item)

        if lead is None:
            skipped += 1
            continue

        leads.append(lead)

    log.info(f"📊 Всего записей в датасете:  {raw_count}")
    log.info(f"   Пропущено (без контактов): {skipped}")
    log.info(f"   Отобрано Revo-лидов:       {len(leads)}")

    return leads


def save_leads(leads: list[dict], filepath: str = OUTPUT_FILE) -> None:
    """
    Сохраняет список лидов в JSON с гарантированной резервной копией.
    """
    try:
        from backup_manager import safe_save_json
        safe_save_json(leads, filepath=filepath, tag="scraper_output")
    except Exception as e:
        log.warning(f"⚠️ Бэкап не сработал, сохраняем напрямую: {e}")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=4)
        log.info(f"💾 Сохранено {len(leads)} лидов → {filepath}")


if __name__ == "__main__":
    try:
        leads = run_scraper()
        if leads:
            save_leads(leads, OUTPUT_FILE)
            log.info(f"🎉 Успешно! Лиды сохранены в {OUTPUT_FILE}")
        else:
            log.warning("⚠️ Список лидов пуст.")
    except Exception as e:
        log.error(f"❌ Ошибка в scraper.py: {e}", exc_info=True)
