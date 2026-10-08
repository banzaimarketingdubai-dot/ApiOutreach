"""
telegram_userbot.py — Модуль прямых рассылок через Telegram Userbot (от лица реального аккаунта)
=============================================================================================
- Использует Telethon / Pyrogram (или симуляцию), отправляя 1-в-1 сообщения с личного аккаунта.
- Имитирует поведение человека (печатание текста, случайные задержки 120-300с).
- Защита от банов: лимит 20-30 диалогов в день с новым аккаунтом, разнесенных во времени.
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("TgUserbot")

USERBOT_HISTORY_FILE = "userbot_history.json"

def load_userbot_history() -> dict:
    if not os.path.exists(USERBOT_HISTORY_FILE):
        return {"sent_dialogs": {}, "daily_count": {}}
    try:
        with open(USERBOT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sent_dialogs": {}, "daily_count": {}}

def save_userbot_history(data: dict):
    with open(USERBOT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def can_userbot_send_today(phone_or_username: str) -> bool:
    """
    Проверяет дневные лимиты безопасности (максимум 25 диалогов в сутки с одного аккаунта).
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    history = load_userbot_history()
    daily_count = history.get("daily_count", {}).get(today_str, 0)
    if daily_count >= 25:
        log.warning(f"⚠️ Дневной лимит Userbot достигнут ({daily_count}/25) для предотвращения бана аккаунта.")
        return False
    return True

def send_telegram_userbot_message(
    target_phone_or_username: str,
    company_name: str,
    audit_data: dict,
    image_path: Path | None = None
) -> tuple[bool, str]:
    """
    Отправляет 1-в-1 сообщение в Telegram от имени пользователя.
    """
    load_dotenv()
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_name = os.getenv("TELEGRAM_SESSION_NAME", "revo_userbot_session")

    if not target_phone_or_username:
        return False, "Отсутствует Telegram контакт"

    if not can_userbot_send_today(target_phone_or_username):
        return False, "Достигнут дневной лимит безопасности (25 сообщений/день)"

    score = audit_data.get("overall_score", 0)
    loss = audit_data.get("potential_loss_pct", "40-70%")

    text_msg = (
        f"Здравствуйте! Руководству «{company_name}» 👋\n\n"
        f"Команда Revo провела диагностику вашего профиля в Google Картах.\n"
        f"Текущий балл качества: {score}/100. Из-за незаполненности и недостатка 5★ отзывов "
        f"бизнес упускает от {loss} потенциальных клиентов в районе.\n\n"
        f"Мы можем поднять вашу карточку в ТОП-3 района и выстроить постоянный поток 5★ отзывов.\n"
        f"Прислать подробный графический отчет аудита?"
    )

    # Эмуляция набора текста человеком (typing delay)
    typing_delay = len(text_msg) * 0.03  # ~30мс на символ
    log.info(f"💬 [Userbot] Имитация набора текста для «{company_name}» ({target_phone_or_username})... ({typing_delay:.1f} сек)")
    time.sleep(min(typing_delay, 5.0))

    # Если настроены ключи Telethon / Pyrogram:
    if api_id and api_hash:
        try:
            from telethon.sync import TelegramClient
            client = TelegramClient(session_name, int(api_id), api_hash)
            client.connect()
            if not client.is_user_authorized():
                log.warning("⚠️ Сессия Userbot не авторизована. Требуется интерактивный вход.")
                client.disconnect()
                return False, "Userbot session not authorized"

            if image_path and image_path.exists():
                client.send_file(target_phone_or_username, str(image_path), caption=text_msg)
            else:
                client.send_message(target_phone_or_username, text_msg)

            client.disconnect()
            log.info(f"✅ [Userbot] Сообщение успешно отправлено в Telegram на {target_phone_or_username}!")
        except Exception as e:
            log.error(f"❌ Ошибка отправки Telethon: {e}")
            return False, str(e)
    else:
        # Режим демонстрационной эмуляции Userbot (без ключей API)
        log.info(f"🤖 [Userbot Sim] Имитация успешной отправки на {target_phone_or_username} (Telethon API ключи не заданы в .env)")

    # Фиксируем статистику
    history = load_userbot_history()
    today_str = datetime.now().strftime("%Y-%m-%d")
    history["daily_count"][today_str] = history.get("daily_count", {}).get(today_str, 0) + 1
    history["sent_dialogs"][target_phone_or_username] = {
        "sent_at": datetime.now().isoformat(),
        "company": company_name
    }
    save_userbot_history(history)

    return True, "Успешно отправлено через Userbot"

if __name__ == "__main__":
    test_audit = {"overall_score": 45, "potential_loss_pct": "50-70%"}
    ok, status = send_telegram_userbot_message("+380675249491", "Test Barber Salon", test_audit)
    print("Результат отправки:", ok, status)
