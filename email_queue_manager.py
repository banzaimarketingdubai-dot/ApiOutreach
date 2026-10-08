"""
email_queue_manager.py — Защита от дубликатов имейлов и умная очередь отправки (Anti-Spam Guard)
=============================================================================================
- Гарантирует, что на 1 имейл отсылается НЕ БОЛЕЕ 1 письма в 24 часа.
- Если на имейл уже отправлено письмо, остальные филиалы/клиники ставятся в очередь.
- Очередные письма планируются на следующий день со случайной паузой (+24ч..+30ч).
"""

import json
import logging
import os
import random
from datetime import datetime, timedelta
import sys

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
log = logging.getLogger("EmailQueue")

QUEUE_FILE = "email_queue.json"
MIN_INTERVAL_HOURS = 24

def load_queue_data() -> dict:
    if not os.path.exists(QUEUE_FILE):
        return {"sent_history": {}, "queue": []}
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sent_history": {}, "queue": []}

def save_queue_data(data: dict):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def can_send_email_now(email: str) -> tuple[bool, str, float]:
    """
    Проверяет, можно ли отправлять письмо на данный имейл прямо сейчас.
    Возвращает (can_send, reason, hours_remaining).
    """
    if not email or "@" not in email:
        return False, "Невалидный имейл", 0.0

    email_key = email.lower().strip()
    data = load_queue_data()
    sent_history = data.get("sent_history", {})

    if email_key in sent_history:
        last_sent_str = sent_history[email_key].get("last_sent_at")
        if last_sent_str:
            try:
                last_sent_dt = datetime.fromisoformat(last_sent_str)
                elapsed_seconds = (datetime.now() - last_sent_dt).total_seconds()
                min_seconds = MIN_INTERVAL_HOURS * 3600

                if elapsed_seconds < min_seconds:
                    remaining_hours = (min_seconds - elapsed_seconds) / 3600.0
                    last_comp = sent_history[email_key].get("last_company", "другой филиал")
                    return False, f"Отправлено для «{last_comp}» (пауза еще {remaining_hours:.1f}ч)", remaining_hours
            except Exception:
                pass

    return True, "Разрешено к отправке", 0.0

def record_email_sent(email: str, company_name: str):
    """
    Записывает факты успешной отправки для активации 24ч защиты.
    """
    email_key = email.lower().strip()
    data = load_queue_data()

    if "sent_history" not in data:
        data["sent_history"] = {}

    data["sent_history"][email_key] = {
        "last_sent_at": datetime.now().isoformat(),
        "last_company": company_name,
        "total_sent": data["sent_history"].get(email_key, {}).get("total_sent", 0) + 1
    }
    save_queue_data(data)
    log.info(f"🛡️ Зафиксирована отправка на {email} («{company_name}»). Пауза 24ч включена.")

def queue_lead_for_later(lead: dict, audit_data: dict, img_path: str = "") -> str:
    """
    Помещает лид с совпадающим имейлом в очередь отправки на завтра (+24ч..+30ч).
    """
    data = load_queue_data()
    if "queue" not in data:
        data["queue"] = []

    # Рассчитываем случайное время отправки на завтра (+24ч..+30ч + случайные минуты)
    delay_hours = 24.0 + random.uniform(1.0, 6.0)
    scheduled_dt = datetime.now() + timedelta(hours=delay_hours)
    scheduled_str = scheduled_dt.strftime("%d.%m.%Y %H:%M")

    queue_item = {
        "company_name": lead.get("company_name", ""),
        "email": lead.get("email", ""),
        "lead_data": lead,
        "audit_data": audit_data,
        "screenshot_path": str(img_path) if img_path else "",
        "scheduled_at": scheduled_dt.isoformat(),
        "scheduled_formatted": scheduled_str,
        "created_at": datetime.now().isoformat()
    }

    data["queue"].append(queue_item)
    save_queue_data(data)
    log.info(f"⏳ Защита дубликатов: лид «{lead.get('company_name')}» на {lead.get('email')} отложен на {scheduled_str}")
    return scheduled_str

def process_due_queue():
    """
    Проверяет отложенную очередь и отправляет имейлы, для которых наступило время отправки.
    """
    data = load_queue_data()
    queue = data.get("queue", [])
    if not queue:
        log.info("📭 Очередь отложенных имейлов пуста.")
        return

    now = datetime.now()
    remaining_queue = []
    sent_count = 0

    for item in queue:
        scheduled_at = datetime.fromisoformat(item["scheduled_at"])
        email = item["email"]
        company = item["company_name"]

        if now >= scheduled_at:
            # Проверяем 24ч правило еще раз
            can_send, reason, _ = can_send_email_now(email)
            if can_send:
                log.info(f"🚀 [Очередь] Отправка отложенного имейла на {email} для «{company}»...")
                from revo_email_dispatcher import send_revo_email
                from pathlib import Path
                img_p = Path(item["screenshot_path"]) if item.get("screenshot_path") else None
                ok, err = send_revo_email(email, item["audit_data"], img_p)
                if ok:
                    record_email_sent(email, company)
                    sent_count += 1
                else:
                    log.error(f"❌ Ошибка отправки из очереди: {err}")
            else:
                log.info(f"⏳ Снова отложено ({reason}): «{company}» -> {email}")
                remaining_queue.append(item)
        else:
            remaining_queue.append(item)

    data["queue"] = remaining_queue
    save_queue_data(data)
    log.info(f"✅ Обработка очереди завершена. Отправлено: {sent_count}, Осталось в очереди: {len(remaining_queue)}")

if __name__ == "__main__":
    process_due_queue()
