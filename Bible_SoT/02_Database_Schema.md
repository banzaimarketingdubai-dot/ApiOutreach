# Структура Базы Данных (PostgreSQL)

Документ описывает схемы данных SQLAlchemy для хранения "Master Data" лидов. Основная цель БД — надежное хранение агрегированных данных и недопущение дублей.

## 1. Ключевые Таблицы (Модели)

### Таблица: `users`
Администраторы и операторы системы.
*   `id` (UUID, PK)
*   `email` (String, Unique)
*   `hashed_password` (String)
*   `role` (Enum: ADMIN, OPERATOR, API_CLIENT)

### Таблица: `campaigns` (ex-Tasks)
Утвержденные AI-Стратегом проекты на сбор данных.
*   `id` (UUID, PK)
*   `campaign_name` (String)
*   `status` (Enum: PENDING, RUNNING, COMPLETED, FAILED)
*   `ai_config` (JSONB) - сгенерированный LLM конфиг (запросы, кастомные поля, правила скоринга)
*   `stats` (JSONB) - статистика (найдено, обновлено, добавлено)
*   `created_at` (DateTime)

### Таблица: `leads` (Golden Record)
Главная карточка компании.
*   `id` (UUID, PK)
*   `company_name` (String, Index)
*   `business_type` (String)
*   `city` (String, Index)
*   `address` (String)
*   `latitude` (Float)
*   `longitude` (Float)
*   `website` (String)
*   `rating` (Float)
*   `reviews_count` (Integer)
*   `revo_score` (Integer) - (0-100)
*   `audit_notes` (Text) - Примечания системы (почему скор низкий)
*   `custom_data` (JSONB) - гибкое поле для результатов AI-скрапинга (ответы LLM на кастомные вопросы)
*   `is_unsubscribed` (Boolean) - Отписался ли лид от рассылки (чтобы не жечь домен)
*   `created_at`, `updated_at` (DateTime)

### Таблица: `contacts`
Связь 1-к-Многим с `leads`. Хранит все контакты гибко.
*   `id` (UUID, PK)
*   `lead_id` (UUID, FK -> leads.id)
*   `contact_category` (Enum: STANDARD, NON_STANDARD)
*   `contact_type` (String, Index) - например: `email`, `phone`, `whatsapp`, `instagram`, `custom_form`
*   `contact_value` (String) - само значение контакта.
*   `source` (String) - откуда взят (например: `gmaps`, `website`, `manual`)
*   `is_primary` (Boolean) - является ли главным для связи.

### Таблица: `outreach_campaigns`
Хранит настройки Drip Campaigns (Холодный аутрич).
*   `id` (UUID, PK)
*   `name` (String) - Имя кампании (напр. "Barbershops Kyiv - Hidden Gems")
*   `prompt_template` (Text) - Системный промпт для генерации писем (StoryBrand)
*   `status` (Enum: DRAFT, ACTIVE, PAUSED, COMPLETED)
*   `created_at` (DateTime)

### Таблица: `email_sequences`
Хранит воронку из 5 касаний для конкретного лида.
*   `id` (UUID, PK)
*   `lead_id` (UUID, FK -> leads.id)
*   `campaign_id` (UUID, FK -> outreach_campaigns.id)
*   `current_touch` (Integer) - Текущий шаг (1-5)
*   `status` (Enum: DRAFT, QUEUED, SENT, OPENED, REPLIED, BOUNCED)
*   `promo_status` (Enum: NONE, CODE_SENT, TRIAL_ACTIVE, CONVERTED, DROPPED, UNSUBSCRIBED)
*   `next_send_date` (DateTime) - Когда отправить следующее письмо
*   `email_content` (Text) - Сгенерированный текст (для ревью)
*   `created_at`, `updated_at` (DateTime)

## 2. Логика Слияния Карточек (Entity Resolution / Deduplication)

Перед `INSERT` нового лида, полученного от парсера, система вызывает сервис `LeadMergerService`.

**Алгоритм поиска дубликата (по приоритету):**
1.  **Match by Phone:** Из сырых данных извлекается телефон, нормализуется (очищается от пробелов/скобок, приводится к +XXX). Поиск в таблице `contacts` где `contact_type='phone'`. Если найдено -> берем `lead_id`.
2.  **Match by Website:** Очистка домена (удаление http/www/углов). Поиск по `leads.website`. Если найдено -> склеиваем.
3.  **Match by Name & Geo:** Если `company_name` совпадает (Levenstein distance < threshold или ILIKE) И координаты (lat, lng) находятся в радиусе 50 метров.

**Действие при слиянии (Merge):**
*   Если поле пустое у старого лида — заполняем новым.
*   Новые контакты добавляются в `contacts` (без дублирования одинаковых `contact_value`).
*   Если у лида появился сайт (а раньше не было) — триггерится задача на `Enrichment` (сбор email/мессенджеров с нового сайта).
