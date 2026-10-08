# 🚀 Revo Master Data Platform & B2B Lead Engine

Автономная B2B система сбора, ИИ-обогащения и квалификации потенциальных лидов (Master Data) под агентские задачи и услуги **Revo**.

---

## 🛠 Новая Архитектура: Revo Master Data Platform (v1.0 SoT)

Система переведена на современный микросервисный стек с веб-интерфейсом и ИИ-ассистентом кампаний (AI Strategist Co-pilot).

### Компоненты платформы:
1. **Backend (FastAPI):** Асинхронный REST API сервер для работы с базой лидов и управлением задачами.
2. **Database (PostgreSQL 15):** Хранилище Golden Record карточек с поддержкой `JSONB` для произвольных ИИ-переменных.
3. **Background Workers (Celery + Redis):** Изолированный конвейер парсинга Google Maps (Apify), проверки мессенджеров и LLM-батчинга (Gemini 3.8 / Grok).
4. **AI Campaign Strategist:** Встроенный ИИ-копилот, формирующий поисковые запросы и схемы кастомных переменных по цели пользователя.
5. **Frontend (React + Vite + Tailwind):** Адаптивный веб-дашборд с интеграцией в Telegram Mini Apps (TMA).

---

## 🚀 Быстрый Запуск

### Запуск через Docker Compose (Рекомендуемый способ):

```bash
docker-compose up --build -d
```

Интерфейс будет доступен по адресу:
- **Веб-дашборд:** `http://localhost:3000`
- **FastAPI Swagger Docs:** `http://localhost:8000/docs`

---

## 📋 Настройка ключей (.env)

Укажите API-ключи в корневом файле `.env`:

```env
# Apify Token (парсинг Google Maps)
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxx

# AI Models (Gemini 3.8 / Grok)
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
GROK_API_KEY=xai-xxxxxxxxxxxxxxxxx

# Database & Redis
POSTGRES_USER=revo_user
POSTGRES_PASSWORD=revo_secret
POSTGRES_DB=revo_masterdata
```

---

## 📊 Порядок взаимодействия с API (Интеграторы):

* `POST /api/v1/ai/strategy` — Запрос к ИИ-Стратегу для генерации концепта кампании.
* `POST /api/v1/campaigns` — Создание и запуск Celery-конвейера сбора.
* `GET /api/v1/leads` — Забор Master Data лидов с фильтрацией по GEO, Revo Score и контактам.
* `GET /api/v1/export/csv` — Экспорт отфильтрованной базы в CSV.

