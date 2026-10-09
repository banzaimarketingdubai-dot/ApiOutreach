# План Интеграции: Каскадный AI-Outreach (Telegram + WhatsApp)

## Цель
Выстроить автоматизированную воронку, которая собирает данные из Apify Outreach, обогащает их, проверяет наличие номеров в мессенджерах (Telegram, WhatsApp) и передает в Lead Radar для рассылки глубоко персонализированных сообщений через юзерботов.

## Фаза 1: Интеграция Чекера Мессенджеров (Apify Outreach)
1. **Расширение базы данных (`Lead`)**:
   - Добавить в `custom_data` или отдельными колонками поля: `has_telegram` (bool), `has_whatsapp` (bool), `messenger_status` (string).
2. **Backend API (`campaigns.py` / `leads.py`)**:
   - Создать эндпоинт `/api/v1/leads/check_messengers` для массовой проверки выбранных лидов.
   - Интегрировать простые скрипты-чекеры (например, через WhatsApp Web API и Telethon/Pyrogram API-ключ для проверки контактов).
3. **Frontend UI (`MasterDataGrid.jsx`)**:
   - Добавить новые фильтры в таблицу: "Только с Telegram", "Только с WhatsApp".
   - Добавить кнопку массового действия: **"Run Messenger Check"**.

## Фаза 2: Синхронизация с Lead Radar
1. **Export API**:
   - Создать эндпоинт `/api/v1/campaigns/export_lead_radar`, который отдает JSON или CSV строго в формате, который ожидает Lead Radar.
   - Либо настроить прямую запись в базу SQLite/PostgreSQL `Lead Radar` (если они на одном сервере).
2. **Генерация Icebreaker'ов**:
   - Передать задачу генерации уникальных Icebreaker (вступлений) на сторону Gemini в Apify Outreach, чтобы в Lead Radar уходили уже готовые связки `[телефон, платформа, готовый_персональный_текст]`.

## Фаза 3: Модернизация Lead Radar (WhatsApp)
1. **Развертывание Evolution API / WAHA**:
   - Поднять Docker-контейнер Evolution API для обеспечения WhatsApp-шлюза (эмуляция WhatsApp Web для юзерботов).
2. **База данных Lead Radar (`B2BProspect`)**:
   - Добавить поле `platform` (enum: `'telegram'`, `'whatsapp'`).
   - В `OutreachAccount` добавить поле `whatsapp_token` / `instance_name`.
3. **Адаптация `outreach_worker.py`**:
   - Обновить воркер: если `platform == 'telegram'`, использовать стандартный `Pyrogram`.
   - Если `platform == 'whatsapp'`, отправлять REST POST запрос на локальный Evolution API (`/message/sendText`).

## Фаза 4: Тестирование и Запуск
1. **Тестовый прогон (Dry Run)**:
   - Прогнать 5 собственных номеров, убедиться что роутинг работает корректно (если номер в ТГ - летит в ТГ, если только в WA - летит в WA).
2. **Боевой запуск (Beauty Kyiv + Dubai)**:
   - Запустить 600 Киевских лидов.
   - Измерить процент доставки и банов юзерботов.

---
**Следующий шаг:** Начать с реализации **Фазы 1** (написание API для чекера мессенджеров на стороне нашего текущего проекта).
