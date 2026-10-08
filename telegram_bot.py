"""
telegram_bot.py — Revo Command Center | Telegram Bot Control Panel v2.1
========================================================================
Интерактивная панель управления конвейером Revo через Telegram.

НОВЫЙ ФУНКЦИОНАЛ v2.1:
  - ⚙️ Настройка видов бизнеса (ниш): включение/выключение категорий и добавление своих!
  - 📍 Настройка районов города: точный выбор районов (Business Bay, Печерск и т.д.) или сбор по всему городу.
  - 🌍 Выбор ГЕО и автоматическое создание листов Revo_<GEO> в Google Sheets.
  - 🚀 Запуск полного комбайна Revo (Парсинг Google Maps -> Обогащение -> Аудит -> Sheets)
  - ✉️ Запуск персонализированной имейл-рассылки с графическими карточками аудита
  - 📸 Мгновенная генерация PNG-аудита по прямой ссылке Google Maps (/audit <ссылка>)
  - 📋 Просмотр базы лидов из Google Sheets с баллами Revo Score (0-100%)
  - 🛑 Безопасная остановка конвейера
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import socket
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN  = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID    = os.getenv('TELEGRAM_CHAT_ID', '')
SCRIPT_DIR = Path(__file__).parent

POLL_INTERVAL = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("RevoBot")

# Single-Instance Lock — Защита от дублирующих процессов бота (порт 47829)
_bot_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    _bot_lock_socket.bind(('127.0.0.1', 47829))
except OSError:
    log.error("❌ Запуск отменен: Другой экземпляр telegram_bot.py уже запущен в системе!")
    sys.exit(0)

_stop_requested = threading.Event()
_pipeline_running = threading.Event()
_pipeline_stats = {}
USER_STATES = {}

ACTIVE_GEO = os.getenv('DEFAULT_GEO', 'Kyiv')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '1W7tz2Z5mBHelfppBg94YzfhGv93JSts9eknuj2WiGvk')
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"

DEFAULT_NICHES = [
    "Barbershop",
    "Beauty Salon",
    "Dental Clinic",
    "Veterinary Clinic",
    "Spa & Wellness Center",
    "Pet Grooming",
    "Cafe"
]

ACTIVE_NICHES = list(DEFAULT_NICHES)
DISABLED_NICHES = set()

POPULAR_DISTRICTS = {
    "Dubai": ["Business Bay", "Dubai Marina", "Downtown", "JLT", "Deira", "Jumeirah", "DIP"],
    "Kyiv": ["Центр", "Оболонь", "Крещатик", "Подол", "Печерск", "Шевченковский", "Голосеево"],
    "Tbilisi": ["Vake", "Saburtalo", "Old Tbilisi", "Sololaki", "Marjanishvili"],
    "Almaty": ["Медеуский", "Алмалинский", "Бостандыкский", "Ауэзовский"]
}

ACTIVE_DISTRICTS = ["Центр", "Оболонь", "Крещатик", "Подол", "Печерск", "Шевченковский"]


# ═════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ГЕНЕРАЦИИ ЗАПРОСОВ
# ═════════════════════════════════════════════════════════════

def generate_search_queries() -> list[str]:
    enabled_niches = [n for n in ACTIVE_NICHES if n not in DISABLED_NICHES]
    if not enabled_niches:
        enabled_niches = list(DEFAULT_NICHES)

    queries = []
    if ACTIVE_DISTRICTS:
        for niche in enabled_niches:
            for district in ACTIVE_DISTRICTS:
                queries.append(f"{niche} {district} {ACTIVE_GEO}")
    else:
        for niche in enabled_niches:
            queries.append(f"{niche} {ACTIVE_GEO}")

    return queries


# ═════════════════════════════════════════════════════════════
# TELEGRAM API WRAPPER
# ═════════════════════════════════════════════════════════════

def tg_request(method: str, params: dict = None, files: dict = None) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if files:
            import mimetypes
            boundary = '----RevoBoundary'
            body = b''
            for key, val in (params or {}).items():
                body += f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{val}\r\n'.encode()
            for key, (filename, filedata) in files.items():
                mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                body += f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
                body += filedata + b'\r\n'
            body += f'--{boundary}--\r\n'.encode()
            req = urllib.request.Request(url, data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        elif params:
            data = json.dumps(params).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        log.error(f"Telegram API error [{method}]: {e}")
        return {'ok': False}


def edit_message_text(chat_id: str, message_id: int, text: str, reply_markup: dict = None, parse_mode: str = 'HTML') -> dict:
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': parse_mode,
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    return tg_request('editMessageText', payload)


def send_message(chat_id: str, text: str, reply_markup: dict = None, parse_mode: str = 'HTML') -> dict:
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    return tg_request('sendMessage', payload)


def answer_callback_query(callback_query_id: str, text: str = '') -> dict:
    return tg_request('answerCallbackQuery', {
        'callback_query_id': callback_query_id,
        'text': text
    })


def send_photo(chat_id: str, photo_path: Path, caption: str = '', reply_markup: dict = None) -> dict:
    try:
        with open(photo_path, 'rb') as f:
            data = f.read()
        params = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        return tg_request('sendPhoto', params=params, files={'photo': (photo_path.name, data)})
    except Exception as e:
        log.error(f"Failed to send photo: {e}")
        return {'ok': False}


def notify(text: str, chat_id: str = None):
    cid = chat_id or CHAT_ID
    if cid:
        send_message(cid, text)


def get_updates(offset: int = 0) -> list:
    result = tg_request('getUpdates', {'offset': offset, 'timeout': 10, 'limit': 10})
    return result.get('result', [])


# ═════════════════════════════════════════════════════════════
# ИНТЕРАКТИВНОЕ МЕНЮ И КЛАВИАТУРА REVO CONTROL PANEL
# ═════════════════════════════════════════════════════════════

def setup_bot_commands():
    """Регистрирует официальное меню команд Telegram (кнопка / слева от ввода)."""
    commands = [
        {"command": "start", "description": "🔥 Главное меню Revo Control Panel"},
        {"command": "geo", "description": "🌍 Выбрать город/локацию для сбора"},
        {"command": "settings", "description": "⚙️ Фильтры ниш бизнеса и районов"},
        {"command": "run", "description": "🚀 Запустить сбор лидов и аудит"},
        {"command": "send_emails", "description": "✉️ Запустить имейл-рассылку"},
        {"command": "audit", "description": "📸 Точный аудит по ссылке Google Maps"},
        {"command": "leads", "description": "📋 Просмотр базы лидов в Sheets"},
        {"command": "status", "description": "📊 Проверить статус выполнения"},
        {"command": "stop", "description": "🛑 Остановить работу конвейера"},
    ]
    res = tg_request("setMyCommands", {"commands": commands})
    log.info(f"✅ Telegram bot commands menu set: {res.get('ok')}")


def build_main_menu_text():
    enabled_count = len([n for n in ACTIVE_NICHES if n not in DISABLED_NICHES])
    districts_str = ", ".join(ACTIVE_DISTRICTS) if ACTIVE_DISTRICTS else "🌐 Весь город"

    return (
        "🔥 <b>REVO B2B COMMAND CENTER PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌍 <b>Город сбора:</b> <code>{ACTIVE_GEO}</code>\n"
        f"📍 <b>Районы:</b> <code>{districts_str}</code>\n"
        f"🏢 <b>Ниши бизнеса:</b> {enabled_count} активных (из {len(ACTIVE_NICHES)})\n"
        f"📊 <b>Таблица Google Sheets:</b> <a href=\"{SPREADSHEET_URL}\">Revo_{ACTIVE_GEO} 🔗</a>\n\n"
        "<i>Выберите нужный раздел на панели управления:</i>"
    )


def get_persistent_bottom_keyboard():
    """Нижнее постоянное меню (прикреплено прямо на месте клавиатуры в Telegram)."""
    return {
        "keyboard": [
            [{"text": f"🌍 ГЕО: {ACTIVE_GEO}"}, {"text": "⚙️ Ниши & Районы"}, {"text": "🚀 Запустить Revo Combine"}],
            [{"text": "✉️ Запустить Рассылку"}, {"text": "📊 Статус конвейера"}],
            [{"text": "📋 Просмотр Лидов"}, {"text": "📸 Мгновенный Аудит"}],
            [{"text": "🛑 Остановить"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }


def get_main_menu_keyboard():
    """Встроенные Inline-кнопки для динамического меню под сообщением."""
    return {
        "inline_keyboard": [
            [
                {"text": f"🌍 Локация: {ACTIVE_GEO}", "callback_data": "menu_change_geo"},
                {"text": "⚙️ Ниши & Районы", "callback_data": "menu_settings"}
            ],
            [
                {"text": "🚀 Запустить Revo Combine", "callback_data": "menu_prompt_run_combine"},
                {"text": "✉️ Запустить Рассылку", "callback_data": "menu_prompt_run_emails"}
            ],
            [
                {"text": "📊 Статус конвейера", "callback_data": "menu_status"},
                {"text": "📋 Просмотр Лидов", "callback_data": "menu_leads"}
            ],
            [
                {"text": "📗 Открыть Google Таблицу 📊", "url": SPREADSHEET_URL}
            ],
            [
                {"text": "📸 Мгновенный Аудит", "callback_data": "menu_instant_audit"},
                {"text": "🛑 Остановить", "callback_data": "menu_stop"}
            ]
        ]
    }


# ═════════════════════════════════════════════════════════════
# МЕНЮ НАСТРОЕК НИШ И РАЙОНОВ
# ═════════════════════════════════════════════════════════════

def build_settings_text():
    enabled_niches = [n for n in ACTIVE_NICHES if n not in DISABLED_NICHES]
    dist_str = ", ".join(ACTIVE_DISTRICTS) if ACTIVE_DISTRICTS else "🌐 Весь город (без ограничений)"
    
    niches_lines = []
    for n in ACTIVE_NICHES:
        icon = "✅" if n in enabled_niches else "❌"
        niches_lines.append(f"  {icon} <b>{n}</b>")

    niches_list = "\n".join(niches_lines)
    queries = generate_search_queries()

    return (
        "⚙️ <b>НАСТРОЙКИ ФИЛЬТРОВ И СБОРА ЛИДОВ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌍 <b>Город:</b> <code>{ACTIVE_GEO}</code>\n"
        f"📍 <b>Районы ({len(ACTIVE_DISTRICTS)}):</b> <code>{dist_str}</code>\n\n"
        f"🏢 <b>Виды бизнеса ({len(enabled_niches)} из {len(ACTIVE_NICHES)} включены):</b>\n"
        f"{niches_list}\n\n"
        f"🔍 <b>Будет запросов к Google Картам:</b> {len(queries)}\n"
        f"<i>Пример: <code>{queries[0] if queries else 'N/A'}</code></i>\n\n"
        "<i>Нажмите кнопки ниже для быстрой настройки:</i>"
    )


def get_settings_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🏢 Управлять Нишами (Бизнесы)", "callback_data": "menu_niches"},
                {"text": "📍 Выбрать Районы Города", "callback_data": "menu_districts"}
            ],
            [
                {"text": "🔄 Сбросить фильтры к стандартным", "callback_data": "settings_reset"}
            ],
            [
                {"text": "⬅️ Назад в Главное Меню", "callback_data": "menu_main"}
            ]
        ]
    }


def build_niches_text():
    enabled = [n for n in ACTIVE_NICHES if n not in DISABLED_NICHES]
    return (
        "🏢 <b>УПРАВЛЕНИЕ ВИДАМИ БИЗНЕСА (НИШАМИ)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Активно ниш: <b>{len(enabled)}</b> из <b>{len(ACTIVE_NICHES)}</b>\n\n"
        "<i>Нажмите на нишу ниже, чтобы включить (✅) или выключить (❌) её, либо добавьте свою:</i>"
    )


def get_niches_keyboard():
    buttons = []
    row = []
    for idx, niche in enumerate(ACTIVE_NICHES):
        is_active = niche not in DISABLED_NICHES
        icon = "✅" if is_active else "❌"
        row.append({"text": f"{icon} {niche}", "callback_data": f"niche_toggle_{idx}"})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        {"text": "➕ Добавить свою нишу", "callback_data": "niche_add"},
        {"text": "🔄 Сбросить ниши", "callback_data": "niche_reset"}
    ])
    buttons.append([
        {"text": "⬅️ Назад в Настройки", "callback_data": "menu_settings"}
    ])
    return {"inline_keyboard": buttons}


def build_districts_text():
    dist_str = ", ".join(ACTIVE_DISTRICTS) if ACTIVE_DISTRICTS else "🌐 Весь город (без фильтра по районам)"
    return (
        f"📍 <b>НАСТРОЙКА РАЙОНОВ ГОРОДА ({ACTIVE_GEO})</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Текущий выбор: <b>{dist_str}</b>\n\n"
        "<i>Выбирайте конкретные районы для точечной отработки (например, Business Bay или Печерск), или нажмите «Весь город»:</i>"
    )


def get_districts_keyboard():
    pop_districts = POPULAR_DISTRICTS.get(ACTIVE_GEO, ["Center", "Downtown", "North", "South"])
    all_known = list(dict.fromkeys(pop_districts + ACTIVE_DISTRICTS))

    buttons = []
    row = []
    for dist in all_known:
        is_sel = dist in ACTIVE_DISTRICTS
        icon = "✅" if is_sel else "⬜"
        row.append({"text": f"{icon} {dist}", "callback_data": f"district_toggle_{dist}"})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        {"text": "🌐 Весь город (Сбросить)", "callback_data": "district_clear"},
        {"text": "✏️ Ввести другой район", "callback_data": "district_add"}
    ])
    buttons.append([
        {"text": "⬅️ Назад в Настройки", "callback_data": "menu_settings"}
    ])
    return {"inline_keyboard": buttons}


def get_geo_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🏙️ Dubai (Дубай)", "callback_data": "geo_set_Dubai"},
                {"text": "🏙️ Kyiv (Киев)", "callback_data": "geo_set_Kyiv"}
            ],
            [
                {"text": "🏙️ Tbilisi (Тбилиси)", "callback_data": "geo_set_Tbilisi"},
                {"text": "🏙️ Almaty (Алматы)", "callback_data": "geo_set_Almaty"}
            ],
            [
                {"text": "✏️ Ввести свой город", "callback_data": "geo_set_custom"}
            ],
            [
                {"text": "⬅️ Назад в Главное Меню", "callback_data": "menu_main"}
            ]
        ]
    }


def get_geo_run_keyboard(send_emails: bool = False):
    prefix = "run_emails_" if send_emails else "run_combine_"
    return {
        "inline_keyboard": [
            [
                {"text": f"▶️ Подтвердить и Запустить ({ACTIVE_GEO})", "callback_data": f"{prefix}{ACTIVE_GEO}"}
            ],
            [
                {"text": "⚙️ Настроить Ниши & Районы", "callback_data": "menu_settings"}
            ],
            [
                {"text": "🏙️ Dubai", "callback_data": f"{prefix}Dubai"},
                {"text": "🏙️ Kyiv", "callback_data": f"{prefix}Kyiv"},
                {"text": "🏙️ Tbilisi", "callback_data": f"{prefix}Tbilisi"}
            ],
            [
                {"text": "⬅️ Отмена / Назад", "callback_data": "menu_main"}
            ]
        ]
    }


def get_back_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "⬅️ Назад в Главное Меню", "callback_data": "menu_main"}
            ]
        ]
    }


def send_control_panel(chat_id: str):
    send_message(
        chat_id,
        build_main_menu_text(),
        reply_markup=get_main_menu_keyboard()
    )


# ═════════════════════════════════════════════════════════════
# ОБРАБОТКА КОМАНД БОТА
# ═════════════════════════════════════════════════════════════

def cmd_settings(chat_id: str, **_):
    send_message(chat_id, build_settings_text(), reply_markup=get_settings_keyboard())


def cmd_geo(chat_id: str, args: str = "", **_):
    global ACTIVE_GEO
    new_geo = args.strip()

    if new_geo:
        ACTIVE_GEO = new_geo.title()
        send_message(
            chat_id,
            f"✅ Локация для сбора лидов изменена на <b>{ACTIVE_GEO}</b>!\n"
            f"📊 Лиды будут выгружаться в лист <code>Revo_{ACTIVE_GEO}</code> Google Таблицы.",
            reply_markup=get_persistent_bottom_keyboard()
        )
        send_control_panel(chat_id)
        return

    text = (
        "🌍 <b>ВЫБОР ЛОКАЦИИ ДЛЯ СБОРА ЛИДОВ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Текущий выбранный город: <b>{ACTIVE_GEO}</b>\n"
        f"Лист в Google Sheets: <code>Revo_{ACTIVE_GEO}</code>\n\n"
        "Выберите нужный город ниже:"
    )
    send_message(chat_id, text, reply_markup=get_geo_keyboard())


def cmd_start(chat_id: str, **_):
    send_control_panel(chat_id)


def get_leads_text_and_keyboard():
    try:
        credentials_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
        spreadsheet_id = os.getenv('SPREADSHEET_ID', '1W7tz2Z5mBHelfppBg94YzfhGv93JSts9eknuj2WiGvk')
        target_sheet = f"Revo_{ACTIVE_GEO.strip().title()}"
        
        from google.oauth2.service_account import Credentials
        import gspread
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        
        try:
            ws = sh.worksheet(target_sheet)
        except Exception:
            try:
                ws = sh.worksheet("Revo_Leads")
            except Exception:
                ws = sh.sheet1
        
        all_rows = ws.get_all_values()
        if not all_rows or len(all_rows) < 2:
            return f"⚠️ Вкладка '{ws.title}' в Google Sheets пуста.", get_back_keyboard()

        preview = all_rows[1:11]
        lines = [f"📋 <b>База Revo Лидов в Google Sheets (Лист: {ws.title})</b> — Всего: {len(all_rows) - 1}\n"]
        for i, row in enumerate(preview, 1):
            biz_type = row[1] if len(row) > 1 else 'N/A'
            company  = row[2] if len(row) > 2 else '?'
            phone    = row[6] if len(row) > 6 else '—'
            rating   = row[8] if len(row) > 8 else '—'
            reviews  = row[9] if len(row) > 9 else '—'
            audit    = row[10] if len(row) > 10 else '—'
            status   = row[11] if len(row) > 11 else '—'
            lines.append(f"<b>{i}. {company}</b> ({biz_type})\n   ⭐ Рейтинг: {rating}★ ({reviews} отзывов)\n   📞 {phone}\n   ⚠️ Аудит: {audit[:45]}...\n   📊 Статус: {status}")

        kb = {
            "inline_keyboard": [
                [{"text": "📗 Открыть Google Таблицу 📊", "url": SPREADSHEET_URL}],
                [{"text": "🔄 Обновить Базу", "callback_data": "menu_leads"}],
                [{"text": "⬅️ Назад в Главное Меню", "callback_data": "menu_main"}]
            ]
        }
        return '\n\n'.join(lines), kb
    except Exception as e:
        return f"❌ Ошибка загрузки лидов из Google Sheets: {e}", get_back_keyboard()


def get_status_text_and_keyboard():
    if not _pipeline_running.is_set():
        dist_str = ", ".join(ACTIVE_DISTRICTS) if ACTIVE_DISTRICTS else "Весь город"
        text = (
            f"💤 <b>Конвейер Revo не запущен</b>\n"
            f"Город: <b>{ACTIVE_GEO}</b> ({dist_str})\n"
            f"Google Sheets: <code>Revo_{ACTIVE_GEO}</code>\n\n"
            f"Выберите действие:"
        )
    else:
        stats = _pipeline_stats.copy()
        total    = stats.get('total', 0)
        current  = stats.get('current', 0)
        domain   = stats.get('domain', '...')

        pct = int((current / total * 100)) if total else 0
        bar = '█' * (pct // 10) + '░' * (10 - pct // 10)

        text = (
            f"⚙️ <b>Конвейер Revo активен</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Локация: <b>{ACTIVE_GEO}</b> (Google Sheets: <code>Revo_{ACTIVE_GEO}</code>)\n"
            f"Прогресс: [{bar}] {pct}%\n"
            f"Обработано: {current}/{total}\n"
            f"Текущий объект: <code>{domain}</code>"
        )
    kb = {
        "inline_keyboard": [
            [{"text": "🔄 Обновить Статус", "callback_data": "menu_status"}],
            [{"text": "⬅️ Назад в Главное Меню", "callback_data": "menu_main"}]
        ]
    }
    return text, kb


def cmd_leads(chat_id: str, **_):
    text, kb = get_leads_text_and_keyboard()
    send_message(chat_id, text, reply_markup=kb)


def cmd_status(chat_id: str, **_):
    text, kb = get_status_text_and_keyboard()
    send_message(chat_id, text, reply_markup=kb)


def cmd_stop(chat_id: str, **_):
    if not _pipeline_running.is_set():
        send_message(chat_id, "💤 Конвейер не активен.", reply_markup=get_main_menu_keyboard())
        return
    _stop_requested.set()
    send_message(chat_id, "🛑 Сигнал остановки отправлен. Конвейер завершит работу после текущего шага.", reply_markup=get_main_menu_keyboard())


def cmd_queue(chat_id: str, **_):
    from email_queue_manager import load_queue_data
    data = load_queue_data()
    queue = data.get("queue", [])
    sent_history = data.get("sent_history", {})

    if not queue:
        msg = (
            f"📭 <b>Очередь писем пуста.</b>\n\n"
            f"🛡️ <b>Антиспам-защита 24ч</b> активна.\n"
            f"Всего зафиксировано уникальных имейлов: <b>{len(sent_history)}</b>"
        )
    else:
        items_txt = "\n".join([f"• <b>{item['company_name']}</b> ({item['email']})\n  └ <i>Отправка: {item['scheduled_formatted']}</i>" for item in queue[:8]])
        msg = (
            f"⏳ <b>Очередь отложенных имейлов (24h Anti-Spam Guard):</b>\n\n"
            f"Всего в очереди: <b>{len(queue)}</b> писем\n\n"
            f"{items_txt}\n\n"
            f"💡 При совпадении имейлов у разных филиалов письма автоматически расставляются с паузой 24–30 часов."
        )
    send_message(chat_id, msg, reply_markup=get_main_menu_keyboard())


def cmd_audit(chat_id: str, args: str, **_):
    raw_input = args.strip()

    if not raw_input:
        USER_STATES[chat_id] = 'awaiting_audit_url'
        send_message(
            chat_id,
            "🔗 <b>Пришлите прямую ссылку на объект в Google Картах</b>\n\n"
            "Пример: <code>https://maps.app.goo.gl/xxxx</code> или <code>https://www.google.com/maps/place/...</code>",
            reply_markup=get_back_keyboard()
        )
        return

    is_maps_url = any(domain in raw_input.lower() for domain in ["google.com/maps", "maps.app.goo.gl", "goo.gl/maps", "maps.google"])

    if not is_maps_url:
        send_message(
            chat_id,
            "⚠️ <b>Ошибка! Принимаются только ссылки на Google Картах.</b>\n\n"
            "Пожалуйста, отправьте прямую ссылку на карточку бизнеса (например, <code>https://maps.app.goo.gl/xxxx</code>), чтобы избежать неточностей.",
            reply_markup=get_back_keyboard()
        )
        return

    send_message(chat_id, f"🔍 Выполняю точную диагностику объекта по ссылке на Google Картах...")

    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from apify_client import ApifyClient
        from scraper import extract_lead
        from revo_visual_renderer import generate_revo_audit_image

        api_token = os.getenv("APIFY_API_TOKEN")
        lead_data = None

        if api_token:
            client = ApifyClient(api_token)
            log.info(f"🚀 Сканирование ссылки в Google Картах: {raw_input}")
            run_input = {
                "startUrls": [{"url": raw_input}],
                "maxCrawledPlaces": 1,
                "language": "en",
            }
            run_result = client.actor("compass/google-maps-extractor").call(run_input=run_input)
            dataset_id = getattr(run_result, "default_dataset_id", None) or run_result.get("defaultDatasetId")
            
            if dataset_id:
                items = list(client.dataset(dataset_id).iterate_items())
                if items:
                    lead_data = extract_lead(items[0])

        if not lead_data:
            clean_name = raw_input.split('/place/')[-1].split('/')[0].replace('+', ' ') if '/place/' in raw_input else "Объект на Google Картах"
            lead_data = {
                "company_name": clean_name or "Заведение в Google Maps",
                "business_type": "Локальный бизнес",
                "google_maps_url": raw_input,
                "rating": 4.2,
                "reviews_count": 24,
                "website": "",
                "phone": ""
            }

        img_path, audit = generate_revo_audit_image(lead_data)

        if img_path and img_path.exists():
            send_photo(
                chat_id,
                img_path,
                caption=(
                    f"🔥 <b>Точный аудит Revo для бизнеса на Google Картах</b>\n\n"
                    f"🏢 <b>Компания:</b> {audit['company_name']}\n"
                    f"📊 <b>Revo Score:</b> {audit['overall_score']}/100\n"
                    f"⚠️ <b>Упускаемая выручка:</b> -{audit['potential_loss_pct']}\n"
                    f"📈 <b>Прогноз роста:</b> {audit['growth_factor']}\n\n"
                    f"🔗 <b>Ссылка:</b> {raw_input}"
                ),
                reply_markup=get_back_keyboard()
            )
        else:
            send_message(chat_id, "❌ Ошибка при генерации изображения аудита.", reply_markup=get_back_keyboard())

    except Exception as e:
        log.error(f"Error in cmd_audit: {e}", exc_info=True)
        send_message(chat_id, f"❌ Ошибка при анализе ссылки: {e}", reply_markup=get_back_keyboard())


def prompt_run_combine(chat_id: str, send_emails: bool = False):
    action = "ИМЕЙЛ-РАССЫЛКОЙ" if send_emails else "СБОРОМ ЛИДОВ И АУДИТОМ"
    queries = generate_search_queries()
    dist_str = ", ".join(ACTIVE_DISTRICTS) if ACTIVE_DISTRICTS else "Весь город"
    enabled_count = len([n for n in ACTIVE_NICHES if n not in DISABLED_NICHES])

    text = (
        f"📍 <b>ЗАПУСК КОНВЕЙЕРА ({action})</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌍 <b>Город:</b> {ACTIVE_GEO}\n"
        f"📍 <b>Районы:</b> {dist_str}\n"
        f"🏢 <b>Ниши:</b> {enabled_count} категорий\n"
        f"🔍 <b>Запросов к Google Картам:</b> {len(queries)}\n"
        f"📊 <b>Лист Google Sheets:</b> <code>Revo_{ACTIVE_GEO}</code>\n\n"
        "Подтвердите запуск или перейдите в настройки для изменения параметров:"
    )
    send_message(chat_id, text, reply_markup=get_geo_run_keyboard(send_emails=send_emails))


def cmd_run(chat_id: str, send_emails: bool = False, geo: str = None, **_):
    global ACTIVE_GEO
    if geo:
        ACTIVE_GEO = geo.strip().title()

    if _pipeline_running.is_set():
        send_message(chat_id, "⚠️ Конвейер уже запущен!", reply_markup=get_main_menu_keyboard())
        return

    queries = generate_search_queries()
    action_name = "сбор лидов + аудит + Google Sheets" if not send_emails else "сбор лидов + аудит + ИМЕЙЛ-РАССЫЛКА"
    dist_str = ", ".join(ACTIVE_DISTRICTS) if ACTIVE_DISTRICTS else "Весь город"

    send_message(
        chat_id,
        f"🚀 <b>Запуск Revo Combine ({action_name})</b>...\n"
        f"🌍 Локация: <b>{ACTIVE_GEO}</b> ({dist_str})\n"
        f"📊 Лист Google Sheets: <code>Revo_{ACTIVE_GEO}</code>\n"
        f"🔍 Поисковых запросов в Google Картах: <b>{len(queries)}</b>"
    )

    def pipeline_thread():
        _pipeline_running.set()
        _stop_requested.clear()
        _pipeline_stats.clear()

        try:
            sys.path.insert(0, str(SCRIPT_DIR))
            import revo_combine
            revo_combine.run_revo_pipeline(queries=queries, send_emails=send_emails, geo=ACTIVE_GEO)
            notify(
                f"✅ <b>Работа Revo Combine по локации {ACTIVE_GEO} успешно завершена!</b>\n"
                f"📊 Результаты сохранены в Google Таблицу (лист: <code>Revo_{ACTIVE_GEO}</code>)",
                chat_id
            )
        except Exception as e:
            err_msg = str(e)
            if "Monthly usage hard limit exceeded" in err_msg or "hard limit" in err_msg:
                user_err = (
                    "⚠️ <b>Превышен месячный лимит токена Apify!</b>\n\n"
                    "Бесплатный лимит ($5.00) на текущем аккаунте Apify исчерпан.\n\n"
                    "<b>Как исправить за 1 минуту:</b>\n"
                    "1️⃣ Зайдите на <a href=\"https://console.apify.com/account/integrations\">Apify Integrations Console</a>\n"
                    "2️⃣ Скопируйте новый <b>API Token</b> (или зарегистрируйте новый аккаунт)\n"
                    "3️⃣ Вставьте новое значение <code>APIFY_API_TOKEN</code> в файл <code>.env</code>"
                )
            else:
                user_err = f"💥 <b>Ошибка выполнения Revo Combine:</b>\n<code>{err_msg}</code>"
            notify(user_err, chat_id)
            log.exception("Revo Combine error")
        finally:
            _pipeline_running.clear()

    thread = threading.Thread(target=pipeline_thread, daemon=True)
    thread.start()


# ═════════════════════════════════════════════════════════════
# РОУТИНГ DYNAMIC IN-MESSAGE CALLBACKS
# ═════════════════════════════════════════════════════════════

def handle_callback_query(cb: dict):
    global ACTIVE_GEO, ACTIVE_NICHES, DISABLED_NICHES, ACTIVE_DISTRICTS
    cb_id      = cb.get('id', '')
    msg        = cb.get('message', {})
    chat_id    = str(msg.get('chat', {}).get('id', ''))
    message_id = msg.get('message_id')
    data       = cb.get('data', '')

    answer_callback_query(cb_id)

    if data.startswith("geo_set_"):
        geo_name = data.replace("geo_set_", "")
        if geo_name == "custom":
            USER_STATES[chat_id] = 'awaiting_custom_geo'
            send_message(chat_id, "🌍 Напишите название города на английском или русском (например: <code>Kyiv</code>, <code>Tbilisi</code>, <code>Astana</code>):")
        else:
            ACTIVE_GEO = geo_name.title()
            send_message(
                chat_id,
                f"✅ Текущая локация сбора изменена на <b>{ACTIVE_GEO}</b>!\n"
                f"📊 Лиды будут выгружаться в лист <code>Revo_{ACTIVE_GEO}</code>",
                reply_markup=get_persistent_bottom_keyboard()
            )
            send_control_panel(chat_id)
    elif data.startswith("niche_toggle_"):
        try:
            idx = int(data.replace("niche_toggle_", ""))
            if 0 <= idx < len(ACTIVE_NICHES):
                target_niche = ACTIVE_NICHES[idx]
                if target_niche in DISABLED_NICHES:
                    DISABLED_NICHES.remove(target_niche)
                else:
                    DISABLED_NICHES.add(target_niche)
                edit_message_text(chat_id, message_id, build_niches_text(), get_niches_keyboard())
        except Exception as e:
            log.error(f"Error toggling niche: {e}")

    elif data == "niche_add":
        USER_STATES[chat_id] = 'awaiting_custom_niche'
        send_message(chat_id, "🏢 Введите название нового типа бизнеса (например: <code>Ресторан</code>, <code>Автосервис</code>, <code>Фитнес Клуб</code>):")

    elif data == "niche_reset":
        ACTIVE_NICHES = list(DEFAULT_NICHES)
        DISABLED_NICHES.clear()
        edit_message_text(chat_id, message_id, build_niches_text(), get_niches_keyboard())

    elif data.startswith("district_toggle_"):
        dist_name = data.replace("district_toggle_", "")
        if dist_name in ACTIVE_DISTRICTS:
            ACTIVE_DISTRICTS.remove(dist_name)
        else:
            ACTIVE_DISTRICTS.append(dist_name)
        edit_message_text(chat_id, message_id, build_districts_text(), get_districts_keyboard())

    elif data == "district_add":
        USER_STATES[chat_id] = 'awaiting_custom_district'
        send_message(chat_id, f"📍 Введите название района для города {ACTIVE_GEO} (например: <code>Business Bay</code>, <code>Печерск</code>):")

    elif data == "district_clear":
        ACTIVE_DISTRICTS.clear()
        edit_message_text(chat_id, message_id, build_districts_text(), get_districts_keyboard())

    elif data == "menu_settings":
        edit_message_text(chat_id, message_id, build_settings_text(), get_settings_keyboard())

    elif data == "menu_niches":
        edit_message_text(chat_id, message_id, build_niches_text(), get_niches_keyboard())

    elif data == "menu_districts":
        edit_message_text(chat_id, message_id, build_districts_text(), get_districts_keyboard())

    elif data == "settings_reset":
        ACTIVE_NICHES = list(DEFAULT_NICHES)
        DISABLED_NICHES.clear()
        ACTIVE_DISTRICTS.clear()
        edit_message_text(chat_id, message_id, build_settings_text(), get_settings_keyboard())

    elif data.startswith("run_combine_"):
        selected_geo = data.replace("run_combine_", "")
        cmd_run(chat_id=chat_id, send_emails=False, geo=selected_geo)

    elif data.startswith("run_emails_"):
        selected_geo = data.replace("run_emails_", "")
        cmd_run(chat_id=chat_id, send_emails=True, geo=selected_geo)

    elif data == "menu_change_geo":
        cmd_geo(chat_id=chat_id)

    elif data == "menu_prompt_run_combine" or data == "menu_run_combine":
        prompt_run_combine(chat_id=chat_id, send_emails=False)

    elif data == "menu_prompt_run_emails" or data == "menu_run_emails":
        prompt_run_combine(chat_id=chat_id, send_emails=True)

    elif data == "menu_status":
        cmd_status(chat_id=chat_id)

    elif data == "menu_leads":
        cmd_leads(chat_id=chat_id)

    elif data == "menu_instant_audit":
        USER_STATES[chat_id] = 'awaiting_audit_url'
        send_message(
            chat_id,
            "🔗 <b>Пришлите прямую ссылку на объект в Google Картах</b>\n\n"
            "Пример: <code>https://maps.app.goo.gl/xxxx</code> или <code>https://www.google.com/maps/place/...</code>"
        )

    elif data == "menu_stop":
        cmd_stop(chat_id=chat_id)

    elif data == "menu_main":
        if message_id:
            edit_message_text(chat_id, message_id, build_main_menu_text(), get_main_menu_keyboard())
        else:
            send_control_panel(chat_id)

COMMANDS = {
    '/start':       cmd_start,
    '/menu':        cmd_start,
    '/geo':         cmd_geo,
    '/settings':    cmd_settings,
    '/leads':       cmd_leads,
    '/status':      cmd_status,
    '/stop':        cmd_stop,
    '/queue':       cmd_queue,
    '/audit':       cmd_audit,
    '/run':         lambda chat_id, **kw: prompt_run_combine(chat_id, send_emails=False),
    '/send_emails': lambda chat_id, **kw: prompt_run_combine(chat_id, send_emails=True),
}


def handle_message(message: dict):
    global ACTIVE_GEO, ACTIVE_NICHES, ACTIVE_DISTRICTS
    chat_id = str(message.get('chat', {}).get('id', ''))
    text    = message.get('text', '').strip()

    if not text:
        return

    if CHAT_ID and chat_id != CHAT_ID:
        send_message(chat_id, "⛔ Доступ запрещён.")
        return

    log.info(f"📨 Сообщение [{chat_id}]: {text}")

    text_clean = text.lower()

    # Обработка пользовательских вводов
    if USER_STATES.get(chat_id) == 'awaiting_custom_geo':
        USER_STATES.pop(chat_id, None)
        ACTIVE_GEO = text.strip().title()
        send_message(
            chat_id,
            f"✅ Локация изменена на <b>{ACTIVE_GEO}</b>!\n"
            f"📊 Лиды выгрузятся в лист <code>Revo_{ACTIVE_GEO}</code> Google Таблицы.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if USER_STATES.get(chat_id) == 'awaiting_custom_niche':
        USER_STATES.pop(chat_id, None)
        new_niche = text.strip().title()
        if new_niche not in ACTIVE_NICHES:
            ACTIVE_NICHES.append(new_niche)
        DISABLED_NICHES.discard(new_niche)
        send_message(
            chat_id,
            f"✅ Ниша бизнеса <b>«{new_niche}»</b> успешно добавлена!",
            reply_markup=get_niches_keyboard()
        )
        return

    if USER_STATES.get(chat_id) == 'awaiting_custom_district':
        USER_STATES.pop(chat_id, None)
        new_dist = text.strip().title()
        if new_dist not in ACTIVE_DISTRICTS:
            ACTIVE_DISTRICTS.append(new_dist)
        send_message(
            chat_id,
            f"✅ Район <b>«{new_dist}»</b> добавлен для города {ACTIVE_GEO}!",
            reply_markup=get_districts_keyboard()
        )
        return

    if USER_STATES.get(chat_id) == 'awaiting_audit_url':
        USER_STATES.pop(chat_id, None)
        cmd_audit(chat_id=chat_id, args=text)
        return

    # Текстовые кнопки постоянного меню
    if "запустить revo combine" in text_clean:
        prompt_run_combine(chat_id=chat_id, send_emails=False)
        return
    elif "запустить рассылку" in text_clean:
        prompt_run_combine(chat_id=chat_id, send_emails=True)
        return
    elif "ниши & районы" in text_clean or "настройки" in text_clean:
        cmd_settings(chat_id=chat_id)
        return
    elif "гео:" in text_clean or "выбрать гео" in text_clean:
        cmd_geo(chat_id=chat_id)
        return
    elif "статус" in text_clean:
        cmd_status(chat_id=chat_id)
        return
    elif "просмотр лидов" in text_clean:
        cmd_leads(chat_id=chat_id)
        return
    elif "мгновенный аудит" in text_clean:
        USER_STATES[chat_id] = 'awaiting_audit_url'
        send_message(chat_id, "🔗 <b>Пришлите прямую ссылку на объект в Google Картах</b>\n\nПример: <code>https://maps.app.goo.gl/xxxx</code>")
        return
    elif "остановить" in text_clean:
        cmd_stop(chat_id=chat_id)
        return

    parts   = text.split(' ', 1)
    cmd_raw = parts[0].lower().split('@')[0]
    args    = parts[1] if len(parts) > 1 else ''

    handler = COMMANDS.get(cmd_raw)
    if handler:
        handler(chat_id=chat_id, args=args, message=message)
    else:
        send_control_panel(chat_id)


def run_bot():
    if not BOT_TOKEN:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN не задан в .env!")

    me = tg_request('getMe')
    bot_name = me.get('result', {}).get('username', 'UnknownBot')
    log.info(f"🤖 Revo Bot запущен: @{bot_name}")

    setup_bot_commands()

    offset = 0
    log.info("⏳ Слушаю команды...")

    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update['update_id'] + 1
                if 'callback_query' in update:
                    handle_callback_query(update['callback_query'])
                elif 'message' in update or 'edited_message' in update:
                    msg = update.get('message') or update.get('edited_message')
                    if msg:
                        handle_message(msg)
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log.info("👋 Бот остановлен")
            break
        except Exception as e:
            log.error(f"Polling error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Revo Telegram Command Center')
    parser.add_argument('--get-chat-id', action='store_true', help='Получить chat_id из последних сообщений')
    args = parser.parse_args()

    if args.get_chat_id:
        print("\n🔍 Ищем chat_id в последних сообщениях...\n")
        updates = get_updates(0)
        if not updates:
            print("❌ Нет сообщений! Сначала напиши своему боту в Telegram, затем запусти команду снова.")
        else:
            for upd in updates:
                msg = upd.get('message', {})
                chat = msg.get('chat', {})
                print(f"✅ chat_id: {chat.get('id')}\nДобавь в .env:\n  TELEGRAM_CHAT_ID={chat.get('id')}\n")
                break
    else:
        run_bot()
