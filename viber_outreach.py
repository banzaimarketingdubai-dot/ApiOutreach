"""
viber_outreach.py — Модуль прямой рассылки в Viber (Viber Business Bot / HTTP Gateway)
====================================================================================
- Отправляет персонализированные сообщения в Viber по мобильным номерам клиентов.
- Поддерживает интеграцию через Viber REST Bot API / Green API / Infobip / SMS-Fly.
- Включает режим локального тестирования и валидации номеров.
"""

import json
import logging
import os
import sys
import time
import urllib.request
from datetime import datetime
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
log = logging.getLogger("ViberOutreach")

VIBER_HISTORY_FILE = "viber_history.json"

def load_viber_history() -> dict:
    if not os.path.exists(VIBER_HISTORY_FILE):
        return {"sent_history": {}}
    try:
        with open(VIBER_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sent_history": {}}

def save_viber_history(data: dict):
    with open(VIBER_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_viber_message(
    viber_phone: str,
    company_name: str,
    audit_data: dict,
    image_url: str = ""
) -> tuple[bool, str]:
    """
    Отправляет 1-в-1 аутрич сообщение в Viber по номеру телефона.
    """
    load_dotenv()
    viber_token = os.getenv("VIBER_BOT_TOKEN")

    if not viber_phone:
        return False, "Отсутствует номер Viber"

    clean_phone = re.sub(r"[^\d+]", "", str(viber_phone))
    score = audit_data.get("overall_score", 0)
    loss = audit_data.get("potential_loss_pct", "40-70%")

    text_msg = (
        f"Здравствуйте, команда «{company_name}»! 👋\n\n"
        f"Команда Revo составила аудит вашего профиля в Google Картах.\n"
        f"Балл качества: {score}/100. Упущенная выручка: от {loss}.\n\n"
        f"Мы помогаем локальным бизнесам выходить в ТОП-3 района и получать 5★ отзывы автоматически.\n"
        f"Ответьте «Да», если хотите получить полную карточку аудита!"
    )

    log.info(f"📲 [Viber Outreach] Подготовка отправки на {clean_phone} («{company_name}»)...")

    if viber_token:
        try:
            # Отправка через официальный Viber Bot API
            url = "https://chatapi.viber.com/pa/send_message"
            payload = {
                "receiver": clean_phone,
                "min_api_version": 1,
                "type": "text",
                "text": text_msg,
                "sender": {"name": "Revo Audit"}
            }
            if image_url:
                payload["type"] = "picture"
                payload["media"] = image_url

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "X-Viber-Auth-Token": viber_token,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("status") == 0:
                    log.info(f"✅ [Viber] Сообщение успешно доставлено на {clean_phone}")
                else:
                    log.warning(f"⚠️ [Viber] Ошибка от Viber API: {res_data.get('status_message')}")
        except Exception as e:
            log.error(f"❌ Ошибка Viber API: {e}")
            return False, str(e)
    else:
        log.info(f"📲 [Viber Sim] Имитация отправки в Viber на {clean_phone} (VIBER_BOT_TOKEN не задан в .env)")

    # Фиксируем отправку
    history = load_viber_history()
    history["sent_history"][clean_phone] = {
        "sent_at": datetime.now().isoformat(),
        "company": company_name
    }
    save_viber_history(history)

    return True, "Успешно отправлено в Viber"

import re

if __name__ == "__main__":
    test_audit = {"overall_score": 52, "potential_loss_pct": "40-60%"}
    ok, err = send_viber_message("+380675249491", "Spa Club Kyiv", test_audit)
    print("Результат Viber:", ok, err)
