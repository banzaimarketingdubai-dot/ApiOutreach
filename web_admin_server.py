"""
web_admin_server.py — Автономный REST API веб-сервер панели управления BanzAI Revo Admin
========================================================================================
- Работает на встроенном Python http.server (без внешних зависимостей)
- Поставляется с гибридным многопоточным сервером ThreadingHTTPServer (порт 5000)
- Предоставляет REST API для CRM, живого мониторинга процессов, логов и 1-click действий
"""

import json
import logging
import os
import re
import socketserver
import subprocess
import sys
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

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
log = logging.getLogger("WebAdmin")

PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_FILE = os.path.join(BASE_DIR, "leads.json")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True

class AdminRequestHandler(BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _send_json(self, data: dict | list, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath: str, content_type: str):
        if not os.path.exists(filepath):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 File Not Found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # 1. Заглавная страница -> Dashboard UI
        if path in ["/", "/index.html"]:
            dashboard_html = os.path.join(BASE_DIR, "templates", "dashboard.html")
            return self._send_file(dashboard_html, "text/html; charset=utf-8")

        # 2. Статические ресурсы (CSS, JS)
        if path.startswith("/static/"):
            rel_path = path.replace("/static/", "")
            full_path = os.path.join(BASE_DIR, "static", rel_path)
            if rel_path.endswith(".css"):
                return self._send_file(full_path, "text/css; charset=utf-8")
            elif rel_path.endswith(".js"):
                return self._send_file(full_path, "application/javascript; charset=utf-8")
            elif rel_path.endswith(".png"):
                return self._send_file(full_path, "image/png")

        # 3. REST API: Список лидов (/api/leads)
        if path == "/api/leads":
            if not os.path.exists(LEADS_FILE):
                return self._send_json({"leads": [], "total": 0})
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)

            # Поиск и фильтрация
            query = params.get("q", [""])[0].lower()
            geo = params.get("geo", [""])[0].lower()
            if query:
                leads = [x for x in leads if query in x.get("company_name", "").lower() or query in x.get("business_type", "").lower() or query in x.get("address", "").lower()]

            return self._send_json({"leads": leads, "total": len(leads)})

        # 4. REST API: Общая статистика (/api/stats)
        if path == "/api/stats":
            total = 0
            with_email = 0
            with_phone = 0
            mobile_messengers = 0

            if os.path.exists(LEADS_FILE):
                with open(LEADS_FILE, "r", encoding="utf-8") as f:
                    leads = json.load(f)
                total = len(leads)
                with_email = sum(1 for x in leads if x.get("email"))
                with_phone = sum(1 for x in leads if x.get("phone"))
                from messenger_checker import is_valid_mobile_number, normalize_phone_number
                for x in leads:
                    clean_p = normalize_phone_number(x.get("phone", ""))
                    is_mob, _ = is_valid_mobile_number(clean_p)
                    if is_mob:
                        mobile_messengers += 1

            queue_count = 0
            if os.path.exists("email_queue.json"):
                try:
                    qdata = json.load(open("email_queue.json", "r", encoding="utf-8"))
                    queue_count = len(qdata.get("queue", []))
                except Exception:
                    pass

            return self._send_json({
                "total_leads": total,
                "with_email": with_email,
                "with_phone": with_phone,
                "email_coverage_pct": round((with_email / total * 100), 1) if total else 0,
                "mobile_messengers_count": mobile_messengers,
                "messenger_coverage_pct": round((mobile_messengers / total * 100), 1) if total else 0,
                "queue_count": queue_count,
                "server_time": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })

        # 5. REST API: Логи в реальном времени (/api/logs)
        if path == "/api/logs":
            log_file = os.path.join(BASE_DIR, "outreach_log.txt")
            lines = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-60:] # последние 60 строк
            return self._send_json({"logs": [line.strip() for line in lines]})

        # 6. REST API: Очередь антиспам (/api/queue)
        if path == "/api/queue":
            queue_file = os.path.join(BASE_DIR, "email_queue.json")
            if os.path.exists(queue_file):
                with open(queue_file, "r", encoding="utf-8") as f:
                    return self._send_json(json.load(f))
            return self._send_json({"queue": [], "sent_history": {}})

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Действие: Запуск парсинга контактов
        if path == "/api/action/run_enrichment":
            log.info("🚀 [Web Admin] Запуск процесса обогащения контактов...")
            subprocess.Popen([sys.executable, "-u", "enrich_contacts.py"], cwd=BASE_DIR)
            return self._send_json({"status": "started", "message": "Процесс обогащения запущен в фоне"})

        # 2. Действие: Экспорт в Google Sheets
        if path == "/api/action/upload_sheets":
            log.info("📊 [Web Admin] Запуск экспорта в Google Sheets...")
            subprocess.Popen([sys.executable, "-c", "from upload_to_sheets import upload_to_sheets; upload_to_sheets(geo='Kyiv')"], cwd=BASE_DIR)
            return self._send_json({"status": "started", "message": "Выгрузка в Google Sheets запущена в фоне"})

        # 3. Действие: Запуск Telegram Userbot
        if path == "/api/action/run_userbot":
            log.info("🤖 [Web Admin] Запуск Telegram Userbot...")
            subprocess.Popen([sys.executable, "-u", "telegram_userbot.py"], cwd=BASE_DIR)
            return self._send_json({"status": "started", "message": "Telegram Userbot запущен"})

        # 4. Действие: Запуск Viber Outreach
        if path == "/api/action/run_viber":
            log.info("📲 [Web Admin] Запуск Viber Outreach...")
            subprocess.Popen([sys.executable, "-u", "viber_outreach.py"], cwd=BASE_DIR)
            return self._send_json({"status": "started", "message": "Viber Outreach запущен"})

        self.send_response(404)
        self.end_headers()

def run_server():
    os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), AdminRequestHandler)
    log.info("=" * 65)
    log.info(f"🌐 ВЕБ-ПАНЕЛЬ АДМИНИСТРАТОРА BANZAI REVO АКТИВИРОВАНА")
    log.info(f"👉 Откройте в браузере: http://localhost:{PORT}")
    log.info("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Остановка веб-сервера.")
        server.server_close()

if __name__ == "__main__":
    run_server()
