import os
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DEFAULT_SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1W7tz2Z5mBHelfppBg94YzfhGv93JSts9eknuj2WiGvk")


def get_gspread_client() -> gspread.Client:
    """
    Initializes and returns an authorized gspread Client.
    Checks:
    1. GOOGLE_SERVICE_ACCOUNT_JSON env var (raw JSON string)
    2. service_account.json in root or current dir
    3. credentials.json in root or current dir
    """
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json and raw_json.strip():
        try:
            info = json.loads(raw_json.strip())
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds)
        except Exception as e:
            logger.warning(f"Failed to load credentials from GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    possible_files = [
        "service_account.json",
        "credentials.json",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "service_account.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "credentials.json"),
        os.path.join(os.getcwd(), "service_account.json"),
        os.path.join(os.getcwd(), "credentials.json"),
    ]

    for filepath in possible_files:
        norm_path = os.path.normpath(filepath)
        if os.path.exists(norm_path):
            try:
                creds = Credentials.from_service_account_file(norm_path, scopes=SCOPES)
                return gspread.authorize(creds)
            except Exception as e:
                logger.warning(f"Failed to initialize credentials from {norm_path}: {e}")

    raise PermissionError(
        "Service Account credentials for Google Sheets not found. "
        "Please provide GOOGLE_SERVICE_ACCOUNT_JSON in environment variables or service_account.json file."
    )


def sanitize_sheet_title(name: str) -> str:
    """
    Google Sheets sheet titles have constraints:
    - Max 100 chars
    - Cannot contain: [ ] * ? : / \
    """
    cleaned = re.sub(r'[\[\]*?:/\\]', '_', name.strip())
    if not cleaned:
        cleaned = "Audience_Export"
    return cleaned[:95]


def build_audience_rows(leads: List[Any], template_config: Optional[Dict[str, Any]] = None) -> List[List[Any]]:
    """
    Modular Template Adapter for exporting Audience leads to Google Sheets.
    Can be easily customized or replaced once the user provides their custom template.
    """
    header = [
        "№",
        "Название компании",
        "Ниша / Тип бизнеса",
        "Город / GEO",
        "Адрес",
        "Веб-сайт",
        "Телефон",
        "Email",
        "WhatsApp",
        "Telegram",
        "Viber",
        "Рейтинг",
        "Отзывы",
        "Revo Score",
        "Статус обогащения",
        "Ссылка Google Maps",
        "Дата добавления",
    ]

    rows = [header]

    for idx, lead in enumerate(leads, start=1):
        contacts = getattr(lead, "contacts", []) or []
        custom_data = getattr(lead, "custom_data", {}) or {}

        # Extract contacts by channel
        phones = [c.contact_value for c in contacts if getattr(c, "contact_type", "") == "phone"]
        emails = [c.contact_value for c in contacts if getattr(c, "contact_type", "") == "email"]
        whatsapps = [c.contact_value for c in contacts if getattr(c, "contact_type", "") == "whatsapp"]
        telegrams = [c.contact_value for c in contacts if getattr(c, "contact_type", "") == "telegram"]
        vibers = [c.contact_value for c in contacts if getattr(c, "contact_type", "") == "viber"]

        # Fallbacks from custom_data or direct lead fields
        main_phone = phones[0] if phones else (getattr(lead, "phone", "") or custom_data.get("phone", ""))
        main_email = emails[0] if emails else (getattr(lead, "email", "") or custom_data.get("email", ""))
        
        wa_display = whatsapps[0] if whatsapps else ("Да" if custom_data.get("whatsapp_available") == "true" or custom_data.get("whatsapp_available") is True else "")
        tg_display = telegrams[0] if telegrams else ("Да" if custom_data.get("telegram_available") == "true" or custom_data.get("telegram_available") is True else "")
        vb_display = vibers[0] if vibers else ("Да" if custom_data.get("viber_available") == "true" or custom_data.get("viber_available") is True else "")

        # Phone formatting for Google Sheets (force string so + prefix is preserved)
        clean_phone = str(main_phone or "").strip()
        phone_val = f"'{clean_phone}" if clean_phone and not clean_phone.startswith("'") else clean_phone

        created_at_dt = getattr(lead, "created_at", None)
        date_str = created_at_dt.strftime("%d.%m.%Y %H:%M") if created_at_dt else ""

        maps_url = custom_data.get("google_maps_url") or custom_data.get("url") or ""

        row = [
            idx,
            getattr(lead, "company_name", "") or "",
            getattr(lead, "business_type", "") or "",
            getattr(lead, "city", "") or "",
            getattr(lead, "address", "") or "",
            getattr(lead, "website", "") or "",
            phone_val,
            main_email or "",
            wa_display or "",
            tg_display or "",
            vb_display or "",
            getattr(lead, "rating", "") if getattr(lead, "rating", None) is not None else "",
            getattr(lead, "reviews_count", "") if getattr(lead, "reviews_count", None) is not None else "",
            getattr(lead, "revo_score", "") if getattr(lead, "revo_score", None) is not None else "",
            custom_data.get("enrichment_status") or "new",
            maps_url,
            date_str
        ]
        rows.append(row)

    return rows


def export_audience_leads_to_google_sheet(
    audience_name: str,
    leads: List[Any],
    spreadsheet_id: Optional[str] = None,
    template_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Exports leads belonging to an Audience into a dedicated Google Sheet tab.
    Creates or updates the sheet, styles the header, formats numbers, and returns the live link.
    """
    client = get_gspread_client()
    target_spreadsheet_id = spreadsheet_id or DEFAULT_SPREADSHEET_ID

    try:
        spreadsheet = client.open_by_key(target_spreadsheet_id)
    except gspread.SpreadsheetNotFound:
        raise PermissionError(
            f"Google Таблица с ID '{target_spreadsheet_id}' не найдена или нет доступа для Service Account."
        )

    sheet_title = sanitize_sheet_title(audience_name)

    # Get or create worksheet for this audience
    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except gspread.WorksheetNotFound:
        # 1000 rows, 20 columns
        worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=max(100, len(leads) + 20), cols=20)

    # Build rows
    rows = build_audience_rows(leads, template_config)

    # Clear and rewrite
    worksheet.clear()
    worksheet.update(rows, value_input_option="USER_ENTERED")

    # Header styling (dark blue background, white bold text, freeze row 1)
    try:
        header_format = {
            "backgroundColor": {"red": 0.08, "green": 0.12, "blue": 0.22},
            "textFormat": {
                "bold": True,
                "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                "fontSize": 10,
            },
            "horizontalAlignment": "CENTER",
        }
        worksheet.format("A1:Q1", header_format)
        worksheet.freeze(rows=1)
    except Exception as fmt_err:
        logger.warning(f"Header formatting warning: {fmt_err}")

    # Column widths & text phone format
    try:
        col_widths = [
            45,   # №
            260,  # Название компании
            180,  # Ниша
            140,  # Город
            220,  # Адрес
            200,  # Веб-сайт
            150,  # Телефон
            200,  # Email
            120,  # WhatsApp
            120,  # Telegram
            120,  # Viber
            80,   # Рейтинг
            90,   # Отзывы
            100,  # Revo Score
            140,  # Статус
            220,  # Google Maps
            130   # Дата
        ]

        requests = []
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
    except Exception as batch_err:
        logger.warning(f"Batch dimension properties warning: {batch_err}")

    sheet_url = f"https://docs.google.com/spreadsheets/d/{target_spreadsheet_id}/edit#gid={worksheet.id}"

    return {
        "status": "success",
        "sheet_url": sheet_url,
        "spreadsheet_id": target_spreadsheet_id,
        "worksheet_id": worksheet.id,
        "sheet_title": sheet_title,
        "leads_exported": len(leads),
        "exported_at": datetime.utcnow().isoformat()
    }
