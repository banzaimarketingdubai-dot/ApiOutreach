"""
upload_to_sheets.py — Автозагрузка лидов Revo из leads.json в Google Sheets
=======================================================================
Требует: файл service_account.json или credentials.json в той же папке.
Поддерживает автосоздание отдельного листа под каждый ГЕО (Revo_Kyiv, Revo_Dubai и т.д.).
"""

import json
import logging
import os
from datetime import datetime

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1W7tz2Z5mBHelfppBg94YzfhGv93JSts9eknuj2WiGvk")
DEFAULT_SHEET_NAME = os.getenv("SHEET_NAME", "Revo_Leads")
LEADS_FILE = "leads.json"
CREDENTIALS_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

if not os.path.exists(CREDENTIALS_FILE) and os.path.exists("credentials.json"):
    CREDENTIALS_FILE = "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def load_leads(filepath: str = LEADS_FILE) -> list[dict]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл {filepath} не найден. Сначала запусти scraper.py")
    with open(filepath, "r", encoding="utf-8") as f:
        leads = json.load(f)
    log.info(f"📂 Загружено {len(leads)} лидов из {filepath}")
    return leads


def filter_clean_leads(leads: list[dict]) -> list[dict]:
    clean = []
    for lead in leads:
        company_name = lead.get("company_name", "").strip()
        if not company_name:
            continue
        clean.append(lead)
    log.info(f"✅ Готово к экспорту лидов: {len(clean)}")
    return clean


def get_or_create_sheet(spreadsheet, sheet_name: str):
    """
    Возвращает или создаёт вкладку в Google Таблице под конкретный ГЕО.
    """
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        log.info(f"📋 Найдена вкладка: '{sheet_name}'")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=15)
        log.info(f"➕ Создана новая вкладка под ГЕО: '{sheet_name}'")
    return worksheet


def build_rows(leads: list[dict]) -> list[list]:
    from messenger_checker import get_messenger_links
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    header = [
        "№",
        "Тип бизнеса",
        "Название компании",
        "Адрес",
        "Ссылка Google Maps",
        "Веб-сайт",
        "Телефон",
        "Email",
        "WhatsApp",
        "Viber",
        "Telegram",
        "Рейтинг",
        "Кол-во отзывов",
        "Проблемы профиля / Аудит",
        "Потенциал Revo",
        "Дата добавления",
    ]

    rows = [header]
    for i, lead in enumerate(leads, start=1):
        raw_phone = str(lead.get("phone", "") or "").strip()
        phone_display = f"'{raw_phone}" if raw_phone and not raw_phone.startswith("'") else raw_phone

        # Получаем ссылки на мессенджеры для мобильного номера
        links = get_messenger_links(raw_phone)
        wa_url = lead.get("whatsapp") or links.get("whatsapp_url", "")
        viber_url = lead.get("viber") or links.get("viber_url", "")
        tg_url = lead.get("telegram") or links.get("telegram_url", "")

        rows.append([
            i,
            lead.get("business_type", "N/A"),
            lead.get("company_name", ""),
            lead.get("address", ""),
            lead.get("google_maps_url", ""),
            lead.get("website", ""),
            phone_display,
            lead.get("email", ""),
            wa_url,
            viber_url,
            tg_url,
            lead.get("rating", 0.0),
            lead.get("reviews_count", 0),
            lead.get("revo_audit_note", ""),
            lead.get("revo_potential", "MEDIUM"),
            timestamp,
        ])

    return rows


def upload_to_sheets(filepath: str = LEADS_FILE, sheet_name: str = None, geo: str = None):
    """
    Экспортирует лиды в Google Таблицу. Если передан `geo`, выгружает в персональный лист `Revo_<GEO>`.
    """
    if geo:
        target_sheet_name = f"Revo_{geo.strip().title()}"
    elif sheet_name:
        target_sheet_name = sheet_name
    else:
        target_sheet_name = DEFAULT_SHEET_NAME

    log.info("🔑 Авторизация Google Service Account...")
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        log.info("✅ Авторизация успешна")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Файл ключей '{CREDENTIALS_FILE}' не найден!"
        )

    log.info(f"📊 Открытие Google Таблицы {SPREADSHEET_ID} (Лист: {target_sheet_name})...")
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        log.info(f"✅ Таблица открыта: '{spreadsheet.title}'")
    except gspread.SpreadsheetNotFound:
        raise PermissionError(
            "Таблица не найдена или отсутствует доступ Service Account!"
        )

    worksheet = get_or_create_sheet(spreadsheet, target_sheet_name)

    raw_leads = load_leads(filepath)
    clean_leads = filter_clean_leads(raw_leads)

    log.info(f"🗑️ Очистка содержимого на листе '{target_sheet_name}'...")
    worksheet.clear()

    rows = build_rows(clean_leads)

    log.info(f"⬆️ Экспорт {len(rows) - 1} Revo-лидов в Google Sheets (Лист: {target_sheet_name})...")
    worksheet.update(rows, value_input_option="USER_ENTERED")

    header_format = {
        "backgroundColor": {"red": 0.15, "green": 0.20, "blue": 0.35},
        "textFormat": {
            "bold": True,
            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
            "fontSize": 10,
        },
        "horizontalAlignment": "CENTER",
    }
    worksheet.format("A1:P1", header_format)

    col_widths = [
        40,   # №
        180,  # Тип бизнеса
        260,  # Название
        220,  # Адрес
        180,  # Ссылка Google Maps
        220,  # Сайт
        140,  # Телефон
        200,  # Email
        190,  # WhatsApp
        190,  # Viber
        190,  # Telegram
        80,   # Рейтинг
        100,  # Отзывы
        300,  # Аудит профиля
        120,  # Потенциал Revo
        130   # Дата
    ]

    requests = []

    # 1. Задаём явный формат ТЕКСТ для колонки Телефон (Колонка G / index 6)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": worksheet.id,
                "startColumnIndex": 6,
                "endColumnIndex": 7,
                "startRowIndex": 0
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "TEXT"
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # 2. Установка ширины колонок
    for idx, width in enumerate(col_widths):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": worksheet.id,
                    "dimension": "COLUMNS",
                    "startIndex": idx,
                    "endIndex": idx + 1
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    spreadsheet.batch_update({"requests": requests})

    log.info(f"🎉 Завершено! {len(clean_leads)} лидов выгружено в лист '{target_sheet_name}'")
    log.info(f"   🔗 https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")


if __name__ == "__main__":
    try:
        upload_to_sheets()
    except Exception as e:
        log.error(f"❌ Ошибка загрузки в Google Sheets: {e}", exc_info=True)
