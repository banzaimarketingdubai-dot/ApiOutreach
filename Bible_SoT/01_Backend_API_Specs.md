# Backend & API Спецификация (FastAPI + Celery)

Этот документ описывает устройство бекенд-части системы для разработчиков.

## 1. Структура Директорий (Backend)
```text
backend/
├── app/
│   ├── api/          # Роутеры FastAPI (v1)
│   ├── core/         # Настройки (Pydantic BaseSettings), Security (JWT)
│   ├── db/           # SQLAlchemy session, migrations (Alembic)
│   ├── models/       # SQLAlchemy ORM модели
│   ├── schemas/      # Pydantic модели (In/Out)
│   ├── services/     # Бизнес-логика (CRUD, Entity Resolution)
│   ├── workers/      # Celery таски и логика скрапинга
│   └── main.py       # Точка входа FastAPI
├── Dockerfile
├── requirements.txt
└── celery_app.py     # Инициализация Celery
```

## 2. Интеграция Celery + Redis
FastAPI не должен блокироваться при ожидании парсинга.
*   **Брокер сообщений:** Redis (порт 6379).
*   **Celery App:** Настроен на использование Redis как `broker_url` и `result_backend`.
*   **Взаимодействие:** FastAPI эндпоинт `/api/v1/tasks/start` вызывает `celery_app.send_task("scrape_pipeline", kwargs={...})`. Возвращает `task_id`.
*   **Трекинг:** Фронтенд поллит (или использует WebSocket) эндпоинт `/api/v1/tasks/{task_id}/status` для отрисовки прогресс-бара.

## 3. Ключевые REST API Эндпоинты

### Авторизация
*   `POST /api/v1/auth/login` -> Выдает JWT токен.

### Задачи (Tasks)
*   `POST /api/v1/tasks/start` -> Инициация сбора (Body: `{sources: ["gmaps"], niches: ["dental"], geo: "Dubai"}`).
*   `GET /api/v1/tasks` -> История запущенных задач (Pagination).
*   `GET /api/v1/tasks/{task_id}/status` -> Статус (Pending, In Progress (X%), Completed, Failed).

### База Лидов (Master Data)
*   `GET /api/v1/leads` -> Получение списка лидов с мощной фильтрацией (Query params: `niche`, `city`, `has_whatsapp=True`, `min_score`, `has_website=True`).
*   `GET /api/v1/leads/{lead_id}` -> Детальная карточка лида со всеми контактами.
*   `PATCH /api/v1/leads/{lead_id}` -> Ручное редактирование лида оператором.
*   `DELETE /api/v1/leads/{lead_id}` -> Удаление/Архивация.

### Экспорт (Внешние интеграции)
*   `GET /api/v1/export/csv` -> Выгрузка CSV файла по заданным фильтрам.

## 4. Требования к коду
*   Строгая типизация (Type Hints).
*   Использование Pydantic v2.
*   Асинхронные сессии базы данных (`AsyncSession` из SQLAlchemy).
*   Обработка ошибок через централизованный Exception Handler FastAPI.
