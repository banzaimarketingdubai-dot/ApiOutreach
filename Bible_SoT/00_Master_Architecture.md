# Revo Master Data Platform: Общая Архитектура и Концепция (Master Document)

Этот документ является **Single Source of Truth (SoT)** для агентов-разработчиков. Платформа представляет собой B2B систему для генерации, агрегации и обогащения лидов (Master Data). 

## 1. Концепция и Роли (JTBD)
Система разработана для внутренних нужд аутрич-агентства (отсутствие биллинга и монетизации на данном этапе).
- **Администратор:** Полный доступ к настройкам системы, ключам API (Apify, 2GIS, OpenAI) и управлению пользователями.
- **Оператор (Менеджер):** Инициирует запуск конвейеров парсинга, работает с базой лидов (Master Data), применяет фильтры, экспортирует данные.
- **Интегратор (API User):** Внешние скрипты (CRM, email-рассыльщики), которые через API `GET` запросы забирают готовые обогащенные лиды.

## 2. Архитектура и Технический Стек
Проект использует микросервисный подход на базе контейнеров:

*   **Backend (Core & API):** `FastAPI` (Python 3.11+). Асинхронный, быстрый, авто-генерация OpenAPI (Swagger).
*   **Database:** `PostgreSQL 15+`. Реляционная СУБД с активным использованием `JSONB` для неструктурированных данных контактов.
*   **ORM:** `SQLAlchemy 2.0` (async mode).
*   **Background Jobs:** `Celery` + `Redis`. Необходим для изоляции долгих задач парсинга (Apify, веб-скрапинг) от быстрых HTTP-ответов FastAPI.
*   **Frontend:** `React` (на базе `Vite`) + `TailwindCSS` + `shadcn/ui`. SPA приложение с адаптацией под Telegram Mini Apps (TMA).
*   **Deployment:** `Docker` & `Docker Compose`. Все сервисы (api, worker, frontend, db, redis) поднимаются одним конфигом.

## 3. Global Data Flow (AI-Driven Campaign)
1.  **Campaign Strategy (AI Co-pilot):** Оператор вводит текстовую цель в UI. Встроенный **AI-Стратег** (Gemini / Grok) генерирует `Campaign JSON Config` (рекомендованные ГЕО, ниши, поисковые запросы, и список **Custom Variables** для сбора с сайтов).
2.  **Queueing:** После утверждения стратегии, FastAPI сохраняет `Campaign` в БД и отправляет задачи (Tasks) в Celery Queue.
3.  **Extraction:** Celery Worker обращается к Apify/2GIS по сформированным AI запросам.
4.  **Entity Resolution (Дедупликация):** Worker проверяет каждого сырого лида по БД. Склейка происходит по: (Нормализованный Телефон OR Домен OR (Название + Радиус 50м)).
5.  **Standard Enrichment:** Базовый сбор email, ссылок на соц. сети, проверка наличия WhatsApp/Telegram по номеру.
6.  **Smart AI Enrichment (Batching):** Скачанные тексты сайтов агрегируются в батчи и отправляются в бесплатные API (Gemini / Grok). LLM извлекает `Custom Variables` (например, `has_booking_link`, `uses_crm`) строго в формате JSON.
7.  **Dynamic Scoring:** Worker рассчитывает `Lead Score` на основе уникальных правил, заданных AI-Стратегом для этой конкретной кампании.
8.  **Storage:** "Золотая запись" (Golden Record) сохраняется/обновляется в PostgreSQL (кастомные поля ложатся в колонку `custom_data` типа JSONB).
9.  **Distribution:** Интегратор или UI забирает готовую базу через API `/api/v1/leads`.
