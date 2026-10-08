"""
instagram_contact_scraper.py — Скрапер имейлов и контактов из профилей Instagram и Lnk.bio / Altegio
==================================================================================================
Парсит публичные описания профилей (Bio), мета-данные и мультиссылки для извлечения имейлов и мессенджеров.
"""

import json
import logging
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("InstaScraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,ru;q=0.8,en-US;q=0.6,en;q=0.5",
}

def extract_contacts_from_text(text: str) -> dict:
    """
    Извлекает имейлы, телефоны, Telegram и WhatsApp из произвольного текста Bio.
    """
    result = {"email": "", "phone": "", "telegram": "", "whatsapp": ""}
    if not text:
        return result

    # 1. Поиск имейла
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}', text)
    if email_match:
        found_email = email_match.group(0).lower().strip()
        if not any(x in found_email for x in ["example", "domain", "instagram", "sentry", "wix"]):
            result["email"] = found_email

    # 2. Поиск телефона
    phone_match = re.search(r'(?:\+?380|\+?971|0)\s*\(?\d{2,3}\)?\s*\d{3}\s*[\s\-]?\d{2}\s*[\s\-]?\d{2}', text)
    if phone_match:
        clean_p = re.sub(r"[^\d+]", "", phone_match.group(0))
        if len(clean_p) >= 9:
            result["phone"] = clean_p

    # 3. Поиск Telegram handle/link
    tg_match = re.search(r'(?:t\.me/|telegram\.me/|@)([a-zA-Z0-9_]{4,32})', text, re.IGNORECASE)
    if tg_match:
        handle = tg_match.group(1)
        if handle.lower() not in ["instagram", "facebook", "gmail", "com", "ua", "kyiv"]:
            result["telegram"] = f"@{handle}"

    # 4. Поиск WhatsApp
    wa_match = re.search(r'wa\.me/(\d+)', text)
    if wa_match:
        result["whatsapp"] = f"+{wa_match.group(1)}"

    return result

def scrape_instagram_profile(url: str) -> dict:
    """
    Парсит публичную страницу профиля Instagram (или Lnk.bio / Taplink) для получения имейлов и мессенджеров.
    """
    contacts = {"email": "", "phone": "", "telegram": "", "whatsapp": "", "bio": ""}
    if not url:
        return contacts

    if "instagram.com" not in url and "lnk.bio" not in url and "taplink" not in url and "mssg.me" not in url:
        return contacts

    log.info(f"📸 Парсинг профиля соцсети: {url}...")

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")

            # Собираем мета-описания (og:description, title, description)
            meta_texts = []
            for meta in soup.find_all("meta"):
                content = meta.get("content", "")
                if content:
                    meta_texts.append(content)

            full_bio_text = " ".join(meta_texts) + " " + soup.get_text(separator=" ")
            contacts["bio"] = full_bio_text[:300]

            extracted = extract_contacts_from_text(full_bio_text)
            contacts.update({k: v for k, v in extracted.items() if v})

            if contacts["email"]:
                log.info(f"   📧 [Insta Email найдено] {url} -> {contacts['email']}")
            if contacts["telegram"]:
                log.info(f"   💬 [Insta Telegram] {url} -> {contacts['telegram']}")
    except Exception as e:
        log.warning(f"   ⚠️ Не удалось спарсить Instagram {url}: {e}")

    return contacts

if __name__ == "__main__":
    test_url = "https://www.instagram.com/main.grooming"
    res = scrape_instagram_profile(test_url)
    print("Результат парсинга Insta:", res)
