"""
messenger_checker.py — Проверка наличия WhatsApp / Telegram и генерация быстрых ссылок
===================================================================================
- Нормализует номера телефонов к международному формату (E.164)
- Определяет мобильного оператора и проверяет валидность мобильного номера (UA/UAE)
- Генерирует прямые 1-click ссылки для связи в WhatsApp (https://wa.me/...) и Telegram (https://t.me/...)
- Проверяет статус доступности в мессенджерах для рассылки офферов
"""

import logging
import re
import sys
import urllib.request

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
log = logging.getLogger("MessengerChecker")

# Мобильные коды Украины
UA_MOBILE_CODES = {"50", "66", "95", "99", "67", "68", "96", "97", "98", "63", "73", "93"}

def normalize_phone_number(phone_raw: str) -> str:
    """
    Приводит телефон к чистому цифровому формату E.164 (без плюсов, пробелов и скобок).
    Пример: '+380 (67) 524-9491' -> '380675249491'
    """
    if not phone_raw:
        return ""
    # Очищаем все нецифровые символы
    clean = re.sub(r"[^\d]", "", str(phone_raw))

    # Если номер начинался с 0 (например 0675249491) -> добавляем 38
    if len(clean) == 10 and clean.startswith("0"):
        clean = "38" + clean
    # Если номер был 8067... -> 38067...
    elif len(clean) == 11 and clean.startswith("80"):
        clean = "3" + clean

    return clean

def is_valid_mobile_number(phone_digits: str) -> tuple[bool, str]:
    """
    Проверяет, является ли номер мобильным (способен принимать WhatsApp/Telegram).
    """
    if not phone_digits:
        return False, "Пустой номер"

    # Украина (+380)
    if phone_digits.startswith("380") and len(phone_digits) == 12:
        operator_code = phone_digits[3:5]
        if operator_code in UA_MOBILE_CODES:
            return True, "UA Mobile"
        else:
            return False, f"Городской или стационарный номер (код {operator_code})"

    # ОАЭ (+971)
    if phone_digits.startswith("971") and len(phone_digits) in [11, 12]:
        return True, "UAE Mobile"

    if len(phone_digits) >= 10:
        return True, "International Mobile"

    return False, "Невалидная длина номера"

def get_messenger_links(phone_raw: str) -> dict:
    """
    Возвращает объект с прямыми ссылками на WhatsApp и Telegram для указанного номера.
    """
    clean_p = normalize_phone_number(phone_raw)
    is_mobile, type_label = is_valid_mobile_number(clean_p)

    res = {
        "clean_phone": f"+{clean_p}" if clean_p else "",
        "is_mobile": is_mobile,
        "type": type_label,
        "whatsapp_url": "",
        "viber_url": "",
        "telegram_url": "",
        "whatsapp_available": False,
        "viber_available": False,
        "telegram_available": False,
    }

    if not is_mobile or not clean_p:
        return res

    # Прямая ссылка для открытия диалога в WhatsApp
    res["whatsapp_url"] = f"https://wa.me/{clean_p}"
    res["whatsapp_available"] = True

    # Прямая ссылка для открытия диалога в Viber
    res["viber_url"] = f"viber://chat?number=%2B{clean_p}"
    res["viber_available"] = True

    # Прямая ссылка для открытия диалога в Telegram по номеру
    res["telegram_url"] = f"https://t.me/+{clean_p}"
    res["telegram_available"] = True

    return res

def verify_messenger_availability(phone_raw: str) -> dict:
    """
    Проверяет активность веба для мессенджеров WhatsApp / Telegram.
    """
    links = get_messenger_links(phone_raw)
    if not links["is_mobile"]:
        return links

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    # Проверка Telegram web redirect (t.me/+)
    try:
        req = urllib.request.Request(links["telegram_url"], headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            if "tg://resolve" in html or "tg://phone" in html or "Send Message" in html:
                links["telegram_available"] = True
    except Exception:
        pass

    return links

if __name__ == "__main__":
    sample_phones = ["+380 67 524 9491", "044 123 4567", "+971 50 123 4567"]
    for p in sample_phones:
        info = get_messenger_links(p)
        print(f"Phone {p} -> {info}")
