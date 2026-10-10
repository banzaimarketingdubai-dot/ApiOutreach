import resend
import os
from dotenv import load_dotenv

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY", "")

# Mock Lead Data
company_name = "Central District Bakery & Coffee"
audit_link = "https://gbpilot-saas.vercel.app/audit/test_123"
unsub_link = "https://api.revo-masterdata.com/api/v1/outreach/webhooks/unsubscribe?lead_id=test_123"
snapshot_img_url = "https://placehold.co/600x400/ef4444/white/png?text=Geo-Grid+Heatmap+Snapshot"

rating = 4.2
reviews_count = 148
unanswered = 44
last_post = 45
biz_type = "пекарне"

html_body = f"""<div style="font-family: sans-serif; font-size: 14px; color: #1f2937; line-height: 1.6; max-width: 600px;">
<p>Здравствуйте, команда <strong>{company_name}</strong>!</p>

<p>Мы проанализировали ваш профиль на Google Картах. У вас хороший рейтинг ({rating} ⭐️ и {reviews_count} отзывов), видно, что вы заботитесь о качестве сервиса.</p>

<p>Но есть техническая проблема: алгоритмы Google пессимизируют ваш профиль прямо сейчас. Мы видим, что у вас <strong>около {unanswered} неотвеченных отзывов</strong>, а последний SEO-пост выходил <strong>более {last_post} дней назад</strong>.</p>

<p><strong>Почему это убивает ваши продажи:</strong> Гугл отдает топовые места тем компаниям, которые проявляют постоянную активность. Пока вы работаете над бизнесом, ваши конкуренты, которые регулярно отвечают на отзывы и публикуют апдейты, забирают ваших клиентов.</p>

<p>Я сгенерировал интерактивную тепловую карту (Geo-Grid) вашего района. Красные зоны — это сектора, где вы проигрываете конкурентам в поиске:</p>

<p style="text-align: center; margin: 25px 0;">
    <a href="{audit_link}" target="_blank">
        <img src="{snapshot_img_url}" alt="Аудит {company_name}" style="width: 100%; max-width: 500px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" />
    </a>
</p>

<p><strong>Как это исправить (Бесплатно):</strong><br>
1. Прямо сегодня ответьте на все {unanswered} отзывов, обязательно используя ключевые слова (например, "{biz_type} в нашем районе").<br>
2. Раз в неделю публикуйте короткий пост с фотографией (с геотегами) о ваших новостях.</p>

<p>Мы понимаем, что у вас нет времени ежедневно изучать новинки алгоритмов Google. Вы должны развивать бизнес, а не сидеть в кабинете Google My Business.</p>

<p>Поэтому мы создали <strong>GBPilot</strong> — ИИ-систему, которая полностью берет ведение профиля на себя. Она автоматически генерирует идеальные SEO-ответы на отзывы и публикует посты 24/7 (с контролем качества и защитой от конкурентов).</p>

<p>Если хотите протестировать ИИ-автопилот бесплатно на 14 дней — просто <strong>ответьте на это письмо</strong>, и я вышлю секретный промокод.</p>

<p>С уважением,<br>Отдел локальной SEO-аналитики REVO</p>

<br><br>
<p style="font-size: 11px; color: #9ca3af;">
    Письмо отправлено на основе публичных данных Google Карт. 
    <a href="{unsub_link}" style="color: #9ca3af; text-decoration: underline;">Отписаться от аналитики</a>
</p>
</div>"""

try:
    response = resend.Emails.send({
        "from": "REVO Analytics <onboarding@resend.dev>",
        "to": ["banzaimarketingdubai@gmail.com"],
        "subject": f"Технический аудит профиля {company_name}",
        "html": html_body
    })
    print(f"Test email sent successfully! Response: {response}")
except Exception as e:
    print(f"Error sending email: {e}")
