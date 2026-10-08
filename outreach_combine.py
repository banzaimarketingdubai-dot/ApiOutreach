"""
outreach_combine.py — BanzAI Marketing Dubai | Cold Outreach Combine v1.0
==========================================================================
Полный конвейер: CSV → Очистка → Скриншот → HTML-письмо с inline-картинкой → Антиспам

АРХИТЕКТУРА:
  Модуль 1: Data Ingestion    — парсинг и очистка leads.csv
  Модуль 2: Visual Engine     — Playwright headless screenshot
  Модуль 3: Email Dispatcher  — smtplib + inline CID image
  Модуль 4: Anti-Spam Guard   — случайные паузы 120–360 сек

НАСТРОЙКА:
  1. Создай .env рядом со скриптом:
       SMTP_HOST=smtp.gmail.com
       SMTP_PORT=587
       SMTP_USER=your@gmail.com
       SMTP_PASS=your_app_password
       SENDER_NAME=Ihor Sher

  2. Подготовь leads.csv с колонками: Company_Name, Website, Email

  3. pip install playwright python-dotenv
     python -m playwright install chromium

  4. python outreach_combine.py

ВНИМАНИЕ: Используй App Password для Gmail (не основной пароль).
           Включи двухфакторную аутентификацию → myaccount.google.com/apppasswords
"""

import csv
import logging
import os
import random
import re
import smtplib
import time
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ─────────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ
# ─────────────────────────────────────────────────────────────

# Путь к файлу с лидами
LEADS_CSV = "leads.csv"

# Папка для скриншотов
SCREENSHOTS_DIR = Path("screenshots")

# Базовый URL сканера — к нему добавляется домен лида
load_dotenv()
SCANNER_BASE_URL = os.getenv("SCANNER_BASE_URL", "https://banzaimarketing.tech/geo?url={domain}")
PLAYWRIGHT_BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", SCANNER_BASE_URL)

# Задержка после скриншота, чтобы анимации отрендерились (мс)
RENDER_WAIT_MS = 4000

# Антиспам-пауза между письмами (секунды)
SLEEP_MIN = 120
SLEEP_MAX = 360

# Тема письма
SUBJECT_TEMPLATE = "AI Visibility Audit for {domain}"

# ─────────────────────────────────────────────────────────────
# ЛОГИРОВАНИЕ
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("outreach_log.txt", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════
# МОДУЛЬ 1: DATA INGESTION — Парсинг и очистка базы лидов
# ═════════════════════════════════════════════════════════════

def clean_domain(raw_url: str) -> str:
    """
    Очищает сырой URL до чистого домена.

    Примеры:
      https://www.albahomes.ae/listings/ → albahomes.ae
      http://abc.com                     → abc.com
      banzai.tech/                       → banzai.tech
    """
    if not raw_url:
        return ""

    # Убираем протокол
    domain = re.sub(r'^https?://', '', raw_url.strip())
    # Убираем www.
    domain = re.sub(r'^www\.', '', domain)
    # Убираем всё после первого слеша (путь, параметры)
    domain = domain.split('/')[0].strip()
    # Убираем trailing точки или пробелы
    domain = domain.rstrip('.')

    return domain.lower()


def load_leads(csv_path: str) -> list[dict]:
    """
    Загружает лидов из CSV.
    Ожидаемые колонки: Company_Name, Website, Email
    Пропускает строки без Email.
    """
    leads = []

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Файл '{csv_path}' не найден!\n"
            "Создай leads.csv с колонками: Company_Name, Website, Email"
        )

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=2):  # 2 = первая строка данных
            company = row.get('Company_Name', '').strip()
            website = row.get('Website', '').strip()
            email   = row.get('Email', '').strip()

            # Пропускаем строки без email
            if not email or '@' not in email:
                log.warning(f"Строка {i}: нет email для «{company}» — пропущено")
                continue

            domain = clean_domain(website)
            if not domain:
                log.warning(f"Строка {i}: не удалось определить домен для «{company}» — пропущено")
                continue

            leads.append({
                'company': company,
                'website': website,
                'email':   email,
                'domain':  domain,
            })

    log.info(f"✅ Загружено {len(leads)} лидов из {csv_path}")
    return leads


# ═════════════════════════════════════════════════════════════
# МОДУЛЬ 2: VISUAL ENGINE — Playwright headless screenshots
# ═════════════════════════════════════════════════════════════

def take_screenshot(domain: str, screenshots_dir: Path) -> Path | None:
    """
    Открывает сканер BanzAI с параметром домена в headless Chromium,
    ждёт рендера и делает скриншот видимой области.

    Возвращает Path к файлу скриншота или None при ошибке.
    """
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshots_dir / f"{domain}.png"

    scan_url = PLAYWRIGHT_BASE_URL.format(domain=domain)
    log.info(f"📸 Скриншот: {scan_url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )

            context = browser.new_context(
                viewport={'width': 1280, 'height': 900},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                )
            )

            page = context.new_page()

            # Открываем страницу сканера
            page.goto(scan_url, wait_until='domcontentloaded', timeout=30_000)

            # Ждём рендера анимаций и динамического контента
            page.wait_for_timeout(RENDER_WAIT_MS)

            # Скриншот всей видимой области
            page.screenshot(path=str(screenshot_path), full_page=False)

            browser.close()

        log.info(f"   ✅ Сохранён: {screenshot_path}")
        return screenshot_path

    except PlaywrightTimeoutError:
        log.error(f"   ❌ Таймаут при загрузке {scan_url}")
        return None
    except Exception as e:
        log.error(f"   ❌ Ошибка скриншота для {domain}: {e}")
        return None


# ═════════════════════════════════════════════════════════════
# МОДУЛЬ 3: EMAIL DISPATCHER — HTML + inline CID скриншот
# ═════════════════════════════════════════════════════════════

def build_html_body(domain: str) -> str:
    """
    Генерирует HTML-тело письма с inline-картинкой через CID.
    Изображение вставляется через src="cid:screenshot_image" — отображается
    прямо в теле письма, без вложений.
    """
    scan_url = SCANNER_BASE_URL.format(domain=domain)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: Arial, sans-serif;
      font-size: 15px;
      line-height: 1.7;
      color: #1a1a1a;
      background: #ffffff;
      max-width: 640px;
      margin: 0 auto;
      padding: 24px;
    }}
    a {{ color: #c5a880; }}
    img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 6px; }}
    .footer {{ margin-top: 32px; border-top: 1px solid #eee; padding-top: 16px; font-size: 13px; color: #666; }}
    strong {{ color: #111; }}
  </style>
</head>
<body>
  <p>Hello!</p>

  <p>Our team at <strong>BanzAI Marketing Dubai</strong> is conducting research on the Dubai real estate market. 
  We analyze how effectively AI engines like ChatGPT and Perplexity scan local players 
  and recommend them to international investors.</p>

  <p>We ran your website <strong>{domain}</strong> through our technical scanner. 
  The diagnostic result shows that AI agents are currently unable to index your property listings database properly.</p>

  <p>
    <img src="cid:screenshot_image" alt="Audit for {domain}" style="max-width:100%; border: 1px solid #ccc;">
  </p>

  <p><em>(Full interactive report: 
    <a href="{scan_url}">{scan_url}</a>)
  </em></p>

  <p><strong>What does this mean in practice?</strong><br>
  When an investor with a budget of $2M+ asks ChatGPT to compare off-plan projects or recommend a reliable local broker, 
  the AI cannot parse your unstructured catalog without machine-readable files (llms.txt). 
  As a result, the neural network redirects the client to your competitors (like fam or Driven), 
  whose data architecture is optimized for AI engines.</p>

  <p>We have compiled a quick PDF checklist for your IT department on how to fix this blind spot 
  in just a couple of hours and capture traffic from AI search engines.</p>

  <p>Simply reply <strong>"Yes"</strong> to this email, and I will send it over right away.</p>

  <div class="footer">
    Best regards,<br>
    <strong>Ihor Sher</strong><br>
    BanzAI Marketing Dubai<br>
    <a href="https://banzaimarketing.tech">https://banzaimarketing.tech</a>
  </div>
</body>
</html>"""



def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    sender_name: str,
    to_email: str,
    domain: str,
    screenshot_path: Path | None,
    sender_email: str = None,
) -> bool:
    """
    Отправляет HTML-письмо с inline CID скриншотом через SMTP.
    Если скриншот недоступен — отправляет письмо без картинки.

    Возвращает True при успехе, False при ошибке.
    """
    subject = SUBJECT_TEMPLATE.format(domain=domain)
    # Если sender_email не задан, используем smtp_user. Но если smtp_user это 'resend', то нужен sender_email
    from_email = sender_email or smtp_user
    if from_email == 'resend':
        from_email = 'onboarding@resend.dev' # дефолтный песочный адрес Resend
    from_addr = f"{sender_name} <{from_email}>"

    # ── Сборка письма ─────────────────────────────────────────
    msg = MIMEMultipart('related')  # 'related' позволяет inline CID
    msg['Subject'] = subject
    msg['From']    = from_addr
    msg['To']      = to_email

    # Основная часть — alternative (plain + html)
    alt_part = MIMEMultipart('alternative')
    msg.attach(alt_part)

    # Plain text fallback (для почтовиков без HTML)
    plain = (
        f"Hello!\n\n"
        f"We analyzed your website {domain} via the BanzAI GEO scanner.\n"
        f"Full report: {SCANNER_BASE_URL.format(domain=domain)}\n\n"
        f"Reply 'Yes' to this email to receive the PDF checklist.\n\n"
        f"Best regards,\n{sender_name}\nBanzAI Marketing Dubai"
    )
    alt_part.attach(MIMEText(plain, 'plain', 'utf-8'))

    # HTML с inline CID
    html_body = build_html_body(domain)
    alt_part.attach(MIMEText(html_body, 'html', 'utf-8'))

    # ── Прикрепляем скриншот как inline CID ───────────────────
    if screenshot_path and screenshot_path.exists():
        with open(screenshot_path, 'rb') as img_file:
            img = MIMEImage(img_file.read(), _subtype='png')
            img.add_header('Content-ID', '<screenshot_image>')
            img.add_header(
                'Content-Disposition', 'inline',
                filename=f"{domain}.png"
            )
            msg.attach(img)
        log.info(f"   🖼️  Скриншот приложен: {screenshot_path.name}")
    else:
        log.warning(f"   ⚠️  Скриншот недоступен — отправляем письмо без картинки")

    # ── SMTP-отправка ─────────────────────────────────────────
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        log.info(f"   ✉️  Sent → {to_email}")
        return True, ""

    except smtplib.SMTPAuthenticationError as e:
        err_msg = f"SMTP Authentication Error: {e}"
        log.error(f"   ❌ {err_msg}")
        return False, err_msg
    except smtplib.SMTPException as e:
        err_msg = f"SMTP Error: {e}"
        log.error(f"   ❌ {err_msg}")
        return False, err_msg
    except Exception as e:
        err_msg = f"Unexpected Error: {e}"
        log.error(f"   ❌ {err_msg}")
        return False, err_msg


# ═════════════════════════════════════════════════════════════
# ИНТЕГРАЦИЯ GOOGLE SHEETS И EMAIL SCRAPER
# ═════════════════════════════════════════════════════════════

import gspread
from google.oauth2.service_account import Credentials
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

def scrape_email_from_website(url: str) -> str:
    """
    Пытается найти email на главной странице сайта лида.
    """
    if not url.startswith('http'):
        url = 'https://' + url

    log.info(f"🔍 Поиск email на {url}...")
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    # Пытаемся зайти на главную
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Ищем email регуляркой
            emails = re.findall(email_regex, html)
            if emails:
                # Исключаем распространенные ложные срабатывания (картинки, файлы)
                filtered = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', 'domain.com'))]
                if filtered:
                    found = list(set(filtered))[0]
                    log.info(f"   ✅ Найдено на главной: {found}")
                    return found

            # Если на главной нет, попробуем поискать ссылку на контакты
            soup = BeautifulSoup(html, 'html.parser')
            contact_links = []
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if 'contact' in href or 'about' in href or 'контакт' in href:
                    contact_links.append(urllib.parse.urljoin(url, a['href']))

            for link in list(set(contact_links))[:2]: # Проверим максимум 2 контактные страницы
                try:
                    log.info(f"   🔍 Проверяем страницу контактов: {link}...")
                    req_c = urllib.request.Request(link, headers=headers)
                    with urllib.request.urlopen(req_c, timeout=7) as resp_c:
                        html_c = resp_c.read().decode('utf-8', errors='ignore')
                        emails_c = re.findall(email_regex, html_c)
                        if emails_c:
                            filtered_c = [e for e in emails_c if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', 'domain.com'))]
                            if filtered_c:
                                found = list(set(filtered_c))[0]
                                log.info(f"   ✅ Найдено в контактах: {found}")
                                return found
                except Exception:
                    continue

    except Exception as e:
        log.warning(f"   ⚠️ Ошибка при парсинге {url}: {e}")
    
    return ""


# ═════════════════════════════════════════════════════════════
# ГЛАВНЫЙ КОНВЕЙЕР
# ═════════════════════════════════════════════════════════════

def run_pipeline(stop_event=None, stats_callback=None, notify_callback=None, screenshot_callback=None):
    """
    Основной метод: запускает весь конвейер от загрузки Google Sheets до отправки писем.
    """
    load_dotenv()

    smtp_host    = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port    = int(os.getenv('SMTP_PORT', '587'))
    smtp_user    = os.getenv('SMTP_USER', '')
    smtp_pass    = os.getenv('SMTP_PASS', '')
    sender_name  = os.getenv('SENDER_NAME', 'Ihor Sher')
    sender_email = os.getenv('SENDER_EMAIL', '')

    spreadsheet_id = os.getenv('SPREADSHEET_ID', '1W7tz2Z5mBHelfppBg94YzfhGv93JSts9eknuj2WiGvk')
    credentials_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')

    def log_notify(text):
        log.info(text)
        if notify_callback:
            notify_callback(text)

    log_notify("=" * 60)
    log_notify("🚀 BanzAI Outreach Combine v1.0 — Запуск конвейера")
    log_notify("=" * 60)

    # Авторизация Google Sheets
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet("Leads")
        log_notify("✅ Успешно подключились к Google Sheets")
    except Exception as e:
        log_notify(f"❌ Ошибка авторизации Google Sheets: {e}")
        return

    # Получаем все значения
    all_rows = ws.get_all_values()
    if not all_rows or len(all_rows) < 2:
        log_notify("⚠️ Таблица Leads пуста.")
        return

    headers = all_rows[0]
    
    # Проверяем колонки
    # Ожидаемые на русском: Компания, Сайт, Телефон, Статус, Дата добавления
    # Если нет колонки "Email" (или "Имейл"), добавим её
    email_col_idx = -1
    status_col_idx = -1
    website_col_idx = -1
    company_col_idx = -1

    for idx, h in enumerate(headers):
        h_lower = h.strip().lower()
        if 'email' in h_lower or 'имейл' in h_lower:
            email_col_idx = idx
        elif 'статус' in h_lower or 'status' in h_lower:
            status_col_idx = idx
        elif 'сайт' in h_lower or 'website' in h_lower or 'url' in h_lower:
            website_col_idx = idx
        elif 'компания' in h_lower or 'company' in h_lower:
            company_col_idx = idx

    # Если Email нет, добавляем
    if email_col_idx == -1:
        log_notify("➕ Добавляем колонку 'Email' в таблицу...")
        ws.insert_cols([['Email']], col=5)
        # Перечитываем данные
        all_rows = ws.get_all_values()
        headers = all_rows[0]
        for idx, h in enumerate(headers):
            h_lower = h.strip().lower()
            if 'email' in h_lower or 'имейл' in h_lower:
                email_col_idx = idx
            elif 'статус' in h_lower or 'status' in h_lower:
                status_col_idx = idx
            elif 'сайт' in h_lower or 'website' in h_lower:
                website_col_idx = idx
            elif 'компания' in h_lower or 'company' in h_lower:
                company_col_idx = idx

    # Сбор лидов из строк
    leads = []
    for row_idx, row in enumerate(all_rows[1:], start=2): # 2-indexed
        # Дополняем строку если она короче заголовков
        while len(row) < len(headers):
            row.append("")
        
        company = row[company_col_idx] if company_col_idx != -1 else ""
        website = row[website_col_idx] if website_col_idx != -1 else ""
        email = row[email_col_idx] if email_col_idx != -1 else ""
        status = row[status_col_idx] if status_col_idx != -1 else ""
        
        # Если статус уже "Отправлено", пропускаем
        if "отправлено" in status.lower():
            continue

        domain = clean_domain(website)
        if not domain:
            continue

        leads.append({
            'row_idx': row_idx,
            'company': company,
            'website': website,
            'email': email,
            'domain': domain
        })

    total = len(leads)
    if total == 0:
        log_notify("✅ Все доступные лиды уже обработаны!")
        return

    log_notify(f"📋 Найдено {total} необработанных лидов")

    sent_ok = 0
    sent_fail = 0
    screenshot_ok = 0

    if stats_callback:
        stats_callback({'total': total, 'current': 0, 'sent_ok': 0, 'sent_fail': 0, 'domain': 'подготовка'})

    for idx, lead in enumerate(leads, 1):
        if stop_event and stop_event.is_set():
            log_notify(f"🛑 Получен сигнал остановки конвейера.")
            break

        row_idx = lead['row_idx']
        domain  = lead['domain']
        company = lead['company']
        email   = lead['email']

        log_notify(f"\n[{idx}/{total}] ────────────────────────────────────────")
        log_notify(f"🏢 Компания: {company}")
        log_notify(f"🌐 Домен:    {domain}")

        if stats_callback:
            stats_callback({'total': total, 'current': idx, 'sent_ok': sent_ok, 'sent_fail': sent_fail, 'domain': domain})

        # Если email пустой, пытаемся его скрапить
        if not email or '@' not in email:
            scraped_email = scrape_email_from_website(domain)
            if scraped_email:
                email = scraped_email
                # Записываем email в Google Sheets
                ws.update_cell(row_idx, email_col_idx + 1, email)
                log_notify(f"💾 Email сохранен в таблицу: {email}")
            else:
                log_notify("⚠️ Email не найден, пропускаем отправку письма.")
                ws.update_cell(row_idx, status_col_idx + 1, "Нет Email")
                continue

        # ── Модуль 2: Скриншот ────────────────────────────────
        screenshot_path = take_screenshot(domain, SCREENSHOTS_DIR)
        if screenshot_path:
            screenshot_ok += 1
            if screenshot_callback:
                screenshot_callback(domain, screenshot_path, idx, total)


        # Отправляем email если SMTP настроен
        err_msg = ""
        if not smtp_user or not smtp_pass:
            log_notify("⚠️ SMTP не настроен в .env! Имитация успешной отправки.")
            success = True
        else:
            success, err_msg = send_email(
                smtp_host    = smtp_host,
                smtp_port    = smtp_port,
                smtp_user    = smtp_user,
                smtp_pass    = smtp_pass,
                sender_name  = sender_name,
                to_email     = email,
                domain       = domain,
                screenshot_path = screenshot_path,
                sender_email = sender_email,
            )

        if success:
            sent_ok += 1
            ws.update_cell(row_idx, status_col_idx + 1, "Отправлено")
            log_notify(f"✅ Успешно отправлено на {email}")
        else:
            sent_fail += 1
            short_err = err_msg[:50] if err_msg else "Ошибка"
            ws.update_cell(row_idx, status_col_idx + 1, f"Ошибка: {short_err}")
            log_notify(f"❌ Ошибка отправки на {email}: {err_msg}")

        if stats_callback:
            stats_callback({'total': total, 'current': idx, 'sent_ok': sent_ok, 'sent_fail': sent_fail, 'domain': domain})

        # Антиспам-пауза (кроме последнего)
        if idx < total and not (stop_event and stop_event.is_set()):
            anti_spam_sleep()

    log_notify("")
    log_notify("=" * 60)
    log_notify("📊 ИТОГ РАССЫЛКИ")
    log_notify(f"   Всего лидов:        {total}")
    log_notify(f"   Скриншоты созданы:  {screenshot_ok}")
    log_notify(f"   Отправлено писем:   {sent_ok} ✅")
    log_notify(f"   Ошибки отправки:    {sent_fail} ❌")
    log_notify("=" * 60)


if __name__ == "__main__":
    try:
        run_pipeline()
    except FileNotFoundError as e:
        log.error(f"❌ Файл не найден: {e}")
    except EnvironmentError as e:
        log.error(f"❌ Конфигурация: {e}")
    except KeyboardInterrupt:
        log.warning("⚠️ Прервано пользователем (Ctrl+C)")
    except Exception as e:
        log.error(f"❌ Непредвиденная ошибка: {e}", exc_info=True)

