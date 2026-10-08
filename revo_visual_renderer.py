"""
revo_visual_renderer.py — Рендерер графической карточки аудита Revo (Playwright HD)
=============================================================================
Генерирует высококачественный PNG-скриншот карточки аудита для вставки в email.
"""

import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

from revo_audit_engine import calculate_revo_score

TEMPLATES_DIR = Path(__file__).parent / "templates"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"


def sanitize_filename(name: str) -> str:
    """Очищает строку для безопасного использования в названии файла."""
    clean = re.sub(r"[^\w\-_]", "_", name)
    return clean.strip("_")[:50]


def render_audit_html(audit: dict) -> str:
    """Подставляет данные аудита в HTML-шаблон."""
    template_path = TEMPLATES_DIR / "revo_audit_card.html"

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Простая замена плейсхолдеров
    html = html.replace("{{company_name}}", str(audit["company_name"]))
    html = html.replace("{{business_type}}", str(audit["business_type"]))
    html = html.replace("{{overall_score}}", str(audit["overall_score"]))
    html = html.replace("{{status_label}}", str(audit["status_label"]))
    html = html.replace("{{status_color}}", str(audit["status_color"]))
    html = html.replace("{{reputation_score}}", str(audit["reputation_score"]))
    html = html.replace("{{completeness_score}}", str(audit["completeness_score"]))
    html = html.replace("{{visibility_score}}", str(audit["visibility_score"]))
    html = html.replace("{{retention_score}}", str(audit["retention_score"]))
    html = html.replace("{{potential_loss_pct}}", str(audit["potential_loss_pct"]))
    html = html.replace("{{growth_factor}}", str(audit["growth_factor"]))

    # Замена списка узких мест (Jinja-style block)
    bottlenecks_html = "".join([f'<li class="bottleneck-item">{b}</li>' for b in audit["bottlenecks"]])
    html = re.sub(r"{%\s*for item in bottlenecks\s*%}.*?{%\s*endfor\s*%}", bottlenecks_html, html, flags=re.DOTALL)

    return html


def generate_revo_audit_image(lead_data: dict) -> tuple[Path | None, dict]:
    """
    Вычисляет аудит Revo и рендерит HD PNG изображение карточки аудита.
    Возвращает (screenshot_path, audit_dict).
    """
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    audit = calculate_revo_score(lead_data)
    company_name = audit["company_name"]
    safe_name = sanitize_filename(company_name)
    screenshot_path = SCREENSHOTS_DIR / f"revo_audit_{safe_name}.png"

    html_content = render_audit_html(audit)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 800})
            page.set_content(html_content, wait_until="domcontentloaded")
            page.wait_for_timeout(500) # пауза для рендеринга стилей
            page.screenshot(path=str(screenshot_path), full_page=False)
            browser.close()

        return screenshot_path, audit
    except Exception as e:
        print(f"❌ Ошибка рендеринга карточки аудита для {company_name}: {e}")
        return None, audit


if __name__ == "__main__":
    test_lead = {
        "company_name": "Barber Shop Elite",
        "business_type": "Barber shop",
        "rating": 4.2,
        "reviews_count": 22,
        "website": "",
        "phone": "+971501234567"
    }
    img_path, audit = generate_revo_audit_image(test_lead)
    print("Generated Image:", img_path)
    print("Audit overall score:", audit.get("overall_score"))
