# План Разработки Системы Outreach (System 3: Omnichannel Outreach Engine)

Этот документ описывает пошаговый технический план реализации системы автоматических рассылок (Drip Funnels) для 3 целевых аудиторий с возможностью ручного управления (JTBD).

---

## Этап 1: Проектирование Базы Данных (Database Schema)

**Цель:** Создать таблицы для хранения шаблонов воронок и отслеживания статуса рассылки каждого лида.

1. **Создание таблицы `EmailSequences` (или `OutreachFunnels`):**
   - `id` (UUID)
   - `lead_id` (FK to Leads)
   - `funnel_type` (Enum: `HIDDEN_GEMS`, `SINKING_GIANTS`, `GHOSTS`)
   - `current_touch` (Integer, default: 0)
   - `status` (Enum: `QUEUED`, `ACTIVE`, `PAUSED`, `REPLIED`, `BOUNCED`, `UNSUBSCRIBED`, `COMPLETED`)
   - `next_send_date` (DateTime)
   - `promo_status` (Enum: `NONE`, `CODE_SENT`, `TRIAL_STARTED`)
2. **Создание таблицы `OutreachTemplates`:**
   - `funnel_type` (Enum)
   - `touch_level` (Integer, 1-5)
   - `subject_template` (String)
   - `body_template` (Text)
   - `ai_prompt_context` (Text) - Контекст для LLM, если шаблон требует персонализации "на лету".
3. **Обновление таблицы `Leads`:**
   - Добавить поле `is_unsubscribed` (Boolean, default: False)
   - Связь `outreach_funnels` (One-to-One / One-to-Many).

---

## Этап 2: Backend логика и LLM-Генератор (FastAPI)

**Цель:** Реализовать логику запуска воронки, паузы и массовой AI-генерации.

1. **Эндпоинты управления воронками (`/api/v1/outreach/...`):**
   - `POST /funnels/start` - Принимает список `lead_ids` и тип воронки. Создает записи в `EmailSequences`, устанавливает `next_send_date = NOW()`.
   - `POST /funnels/pause` - Ставит `status = PAUSED` для выбранных лидов.
   - `POST /funnels/resume` - Возвращает статус в `ACTIVE`.
   - `POST /funnels/override` - Сохраняет кастомный текст (сгенерированный вручную) и отправляет вне очереди (Job 14).
2. **Интеграция с Groq 120b (Массовая Генерация):**
   - Обновить Celery Worker `generate_outreach_drafts`.
   - Worker должен брать пачку лидов со статусом `QUEUED` (Touch 1), прогонять их данные через `OutreachTemplates` -> `Groq 120b`, получать JSON (email, tg, wa) и сохранять сгенерированные тексты в базу (или сразу ставить в очередь отправки).

---

## Этап 3: Движок отправки и Автоматизация (Celery Beat)

**Цель:** Система должна жить своей жизнью, проверять расписание и отправлять письма 24/7.

1. **Celery Task: `process_outreach_queue` (Cron: каждые 5 минут):**
   - **Шаг 1:** Ищет все записи в `EmailSequences` где `status = ACTIVE` и `next_send_date <= NOW()`.
   - **Шаг 2:** Если текст письма требует генерации, вызывает функцию AI-генератора.
   - **Шаг 3:** Отправляет письмо через **Resend API**.
   - **Шаг 4:** Обновляет `current_touch += 1`. Устанавливает новый `next_send_date` (например, +3 дня для Touch 2, +4 дня для Touch 3). Если `current_touch > 5`, статус `COMPLETED`.
2. **Лимиты и Защита:**
   - Ограничить скорость отправки (Rate Limiting) через Resend до 3-5 писем в минуту для прогрева домена.
   - Проверка `lead.is_unsubscribed == True` перед каждой отправкой.

---

## Этап 4: Webhooks и Авто-Стоп (Resend Integration)

**Цель:** Автоматически останавливать спам, если клиент ответил.

1. **Эндпоинт `/api/webhooks/resend`:**
   - Валидация подписи (Signature verification).
   - **Событие `email.replied`:** 
     - Найти лида по ID (переданному в тэгах или headers).
     - `UPDATE EmailSequences SET status = 'REPLIED'`.
     - Опционально: Отправить автоответ с промокодом `Welcome14` (горячая воронка).
   - **Событие `email.bounced`:** `status = 'BOUNCED'`.
   - **Событие `email.opened`:** Опциональное обновление метрик открываемости.
2. **Unsubscribe Link:**
   - Ссылка в письме: `https://gbpilot.com/unsubscribe?lead_id=1234`.
   - При переходе меняет `is_unsubscribed = True` и останавливает воронку.

---

## Этап 5: Frontend UI (Управление кампанией)

**Цель:** Дать оператору (Админу) удобный пульт управления.

1. **MasterDataGrid (Таблица лидов):**
   - Добавить колонки: `Funnel Status` (Badge: Cold, Paused, Replied, Bounced), `Touch #`.
   - Добавить действия в Action Menu: "Start Funnel", "Pause Funnel", "Resume".
2. **Funnel Setup Modal:**
   - Модальное окно при массовом выборе лидов.
   - Выбор аудитории: "Hidden Gems", "Sinking Giants", "Ghosts".
   - Предпросмотр первого письма (Touch 1).
3. **Обновление Omnichannel Outreach Modal (Оверрайд):**
   - Если оператор открывает модалку для лида, который **уже** в воронке, показать плашку: `⚠️ Lead is in sequence (Touch 2). Manual sending will override and pause the automatic sequence.`
   - Сохранение функционала кнопки `Regenerate with AI` для ручных персонализированных касаний.

---

## Порядок Разработки (Roadmap):

- **Спринт 1:** Backend (Database schema, Models) + Эндпоинты старта/остановки.
- **Спринт 2:** Celery Queue Scheduler + Интеграция с Resend API (отправка писем).
- **Спринт 3:** Webhooks от Resend (Авто-стоп при ответе + Unsubscribe).
- **Спринт 4:** Frontend UI (Колонки в таблице, массовые действия, Funnel Selector).
- **Спринт 5:** AI-Генератор шаблонов для 3 аудиторий (Настройка промптов).
- **Спринт 6:** Sandbox Modal и Manual Lead Creation.
- **Спринт 7:** Analytics Dashboard (Open Rate, Click Rate, Drop-off).
- **Спринт 8 (Запланировано):** Google OAuth Авторизация для админов (Ограничение доступа).- **Спринт 6:** Sandbox Modal и Manual Lead Creation.
- **Спринт 7:** Analytics Dashboard (Open Rate, Click Rate, Drop-off).
- **Спринт 8 (Запланировано):** Google OAuth Авторизация для админов (Ограничение доступа).

---
*Документ автоматически поддерживается и обновляется.*
