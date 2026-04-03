# Архитектура и планы развития

## Текущая архитектура

Проект построен как практичный конвейер поздравлений, а не как fully autonomous agent.

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI |
| База данных | SQLite + SQLAlchemy 2.x |
| Web UI | Jinja2 templates + Bootstrap |
| Текстовая генерация | Template fallback / GigaChat |
| Генерация изображений | Pillow / GigaChat |
| Конфигурация | `.env` + Pydantic settings |

## Основные модули

- `backend/app/agent/` — оркестратор, prompt-building, semantic-layer, GigaChat providers.
- `backend/app/services/` — импорт, enrichment, delivery, holidays, manual events, feedback.
- `backend/app/web/` — веб-интерфейс и operator flow.
- `backend/app/api/` — API endpoints.
- `backend/app/db/` — модели данных и связи сущностей.

## Как работает система сейчас

1. Источник данных формирует клиентский профиль: demo seed, CSV или enrichment через `DaData`.
2. Для клиента появляется `Event`: день рождения, праздник или ручной повод.
3. Агент собирает факты и семантику события.
4. Генератор создаёт текст и иллюстрацию.
5. Результат проходит через approve/delivery flow.
6. Run, delivery и feedback сохраняются для audit и дальнейшего улучшения.

## Направления развития

### 1. Качество и стабильность

- Усиление prompt-building и guardrails.
- Расширение тестового покрытия на критические сценарии.
- Повышение предсказуемости image-generation и delivery fallback.

### 2. Интеграции

- Подключение более реальных источников клиентских данных.
- Расширение каналов доставки.
- Развитие enrichment поверх текущего `demo/dadata/hybrid` слоя.

### 3. AI-возможности

- Использование feedback для более умного выбора tone/style.
- Более точная персонализация по истории взаимодействий и бизнес-контексту.
- Переход от rule-heavy prompt-building к более гибкому planning-слою, если проект реально вырастет по сложности.

Подробный стартовый backlog вынесен в `docs/ISSUES_BOOTSTRAP.md`.
