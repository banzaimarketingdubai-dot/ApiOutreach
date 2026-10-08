"""
revo_email_dispatcher.py — Отправка персонализированных HTML-писем Revo
========================================================================
Генерирует письма с встроенным CID изображения аудита и отправляет через SMTP.
"""

import os
import logging
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("RevoEmail")


def build_revo_html_body(audit: dict, contacts_info: str = None) -> str:
    company = audit.get("company_name", "компании")
    overall_score = audit.get("overall_score", 0)
    rating = audit.get("rating", 0.0)
    reviews_count = audit.get("reviews_count", 0)
    loss_pct = audit.get("potential_loss_pct", "40-70%")
    growth = audit.get("growth_factor", "+2x")

    bottlenecks_html = "".join([f"<li style='margin-bottom:6px;'>⚠️ {b}</li>" for b in audit.get("bottlenecks", [])])

    contacts = contacts_info or (
        "📞 <strong>WhatsApp/Телефон</strong>: +7 (900) 000-00-00<br>"
        "💬 <strong>Telegram</strong>: @RevoSupport"
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: Arial, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      color: #1E293B;
      background: #F8FAFC;
      margin: 0; padding: 20px;
    }}
    .card {{
      max-width: 650px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 12px;
      padding: 32px;
      margin: 0 auto;
    }}
    h2 {{ color: #0F172A; margin-top: 0; }}
    .highlight-box {{
      background: #F1F5F9;
      border-left: 4px solid #6366F1;
      padding: 16px;
      margin: 20px 0;
      border-radius: 4px;
    }}
    .btn {{
      display: inline-block;
      background: #6366F1;
      color: #FFFFFF;
      padding: 12px 24px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: bold;
      margin-top: 16px;
    }}
    .footer {{
      margin-top: 30px;
      padding-top: 16px;
      border-top: 1px solid #E2E8F0;
      font-size: 13px;
      color: #64748B;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Здравствуйте, команда {company}!</h2>
    
    <p>Команда <strong>Revo</strong> провела локальный аудит бизнесов вашей сферы на Google Картах.</p>
    
    <p>Мы проанализировали профиль <strong>{company}</strong> и зафиксировали балл качества: 
       <strong style="color: #6366F1; font-size: 18px;">{overall_score} из 100</strong> 
       ({rating}★, {reviews_count} отзывов).</p>
    
    <p>Ниже представлен графический отчёт диагностики вашего профиля:</p>
    
    <p style="text-align:center; margin: 24px 0;">
      <img src="cid:audit_screenshot" alt="Аудит {company}" style="max-width:100%; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    </p>

    <div class="highlight-box">
      <strong>⚠️ Выявленные точки упущенной выручки:</strong>
      <ul style="margin-top: 8px; padding-left: 20px;">
        {bottlenecks_html}
      </ul>
      <p style="margin-bottom: 0;">Из-за этих факторов бизнес теряет <strong>от {loss_pct} потенциальных клиентов</strong>, отдавая их конкурентам в районе.</p>
    </div>

    <h3>🚀 Как комплекс Revo решает эту задачу:</h3>
    <ul>
      <li>Увеличивает поток позитивных 5★ отзывов на Google Картах в автоматическом режиме.</li>
      <li>Внедряет мобильную систему лояльности для роста Retention Rate (повторных продаж).</li>
      <li>Обеспечивает региональное доминирование и поток новых клиентов уже со следующей недели.</li>
    </ul>

    <p>Будем рады помочь вашему бизнесу занять лидирующие позиции в локации!</p>
    
    <p>Ответьте на это письмо <strong>«Да»</strong> или свяжитесь с нами прямо сейчас:</p>
    <p>{contacts}</p>

    <div class="footer">
      С уважением,<br>
      <strong>Команда Revo Marketing</strong><br>
      <a href="https://revo.marketing">https://revo.marketing</a>
    </div>
  </div>
</body>
</html>"""


def send_revo_email(
    to_email: str,
    audit: dict,
    screenshot_path: Path | None = None
) -> tuple[bool, str]:
    load_dotenv()
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    sender_name = os.getenv("SENDER_NAME", "Revo Team")
    sender_email = os.getenv("SENDER_EMAIL", "")

    if not smtp_user or not smtp_pass:
        log.warning("⚠️ SMTP не настроен в .env! Имитация успешной отправки.")
        return True, "Имитация (SMTP не настроен)"

    company = audit.get("company_name", "")
    loss_pct = audit.get("potential_loss_pct", "40-70%")
    subject = f"[Аудит] {company}: ваш профиль на Google Картах теряет до {loss_pct} клиентов"

    from_email = sender_email or smtp_user
    if from_email == "resend":
        from_email = "onboarding@resend.dev"
    from_addr = f"{sender_name} <{from_email}>"

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email

    alt_part = MIMEMultipart("alternative")
    msg.attach(alt_part)

    # Plain text fallback
    plain_text = f"Здравствуйте, {company}!\nАудит Revo: ваш балл профиля {audit.get('overall_score')}/100. Потеря клиентов: {loss_pct}.\nСвяжитесь с нами для детального отчета."
    alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))

    # HTML body
    html_body = build_revo_html_body(audit)
    alt_part.attach(MIMEText(html_body, "html", "utf-8"))

    # Inline Screenshot Image
    if screenshot_path and screenshot_path.exists():
        with open(screenshot_path, "rb") as img_file:
            img = MIMEImage(img_file.read(), _subtype="png")
            img.add_header("Content-ID", "<audit_screenshot>")
            img.add_header("Content-Disposition", "inline", filename=screenshot_path.name)
            msg.attach(img)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        log.info(f"   ✉️  Успешно отправлено Revo-письмо на {to_email}")
        return True, ""
    except Exception as e:
        err_msg = str(e)
        log.error(f"   ❌ Ошибка отправки на {to_email}: {err_msg}")
        return False, err_msg
