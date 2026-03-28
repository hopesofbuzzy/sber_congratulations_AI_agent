# Project Overview — Sber Congratulations AI Agent

Краткий проектный обзор для быстрого входа в репозиторий без внутренних рабочих заметок.

## TL;DR

Проект реализует MVP+ конвейера поздравлений: события -> enrichment профиля клиента/компании -> генерация текста и иллюстрации -> доставка -> логирование и feedback.

Поддерживаются:
- офлайн-режим с fallback-шаблонами;
- интеграция с `GigaChat` для текста и изображений;
- импорт условной базы компаний из CSV;
- enrichment компаний через `demo` / `dadata` / `hybrid`;
- web UI и API для операторского контроля.

## Быстрый старт

1. Установка:

```bat
scripts\setup_backend.cmd
```

2. Запуск UI и API:

```bat
scripts\run_backend.cmd
```

3. Базовый demo-flow:
- `Seed demo data`
- `Enrich company profiles`
- `Run agent now`
- проверка страниц `Clients`, `Events`, `Greetings`, `Deliveries`, `Runs`

## Основные режимы

Настройка идёт через `backend/.env`.

- `LLM_MODE=template|gigachat`
- `IMAGE_MODE=pillow|gigachat`
- `DELIVERY_SCHEDULE_MODE=event_date|immediate`
- `COMPANY_ENRICHMENT_PROVIDER=demo|dadata|hybrid`

## Карта кода

- Точка входа: `backend/app/main.py`
- Web UI: `backend/app/web/router.py`, `backend/app/web/templates/*`
- API: `backend/app/api/*`
- БД и модели: `backend/app/db/models.py`
- Оркестратор: `backend/app/agent/orchestrator.py`
- Генерация текста: `backend/app/agent/generator.py`
- Prompt-building и семантика: `backend/app/agent/llm_prompts.py`, `backend/app/agent/event_semantics.py`
- GigaChat: `backend/app/agent/gigachat_client.py`, `backend/app/agent/gigachat_providers.py`
- Enrichment компаний: `backend/app/services/company_enrichment.py`, `backend/app/services/company_import.py`, `backend/app/services/dadata_client.py`
- Каталог поводов: `backend/app/services/holiday_catalog.py`, `backend/app/services/manual_events.py`
- Отправка: `backend/app/services/sender.py`, `backend/app/services/email_rendering.py`
- Feedback loop: `backend/app/services/feedback.py`

## Что важно знать

- Архитектурные решения и причины собраны в `docs/DECISIONS.md`.
- Внутренние runtime-данные и секреты не хранятся в Git: `backend/.env`, `backend/data/`.
- Для SMTP используется `multipart/alternative`: plain-text fallback + HTML-письмо с inline-иллюстрацией.
