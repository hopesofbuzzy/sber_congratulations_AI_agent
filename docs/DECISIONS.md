# DECISIONS (ADR-lite)

Короткий список ключевых архитектурных решений и причин.  
Нужен, чтобы новый чат/участник команды быстро понял “почему так”.

## 1) Офлайн по умолчанию

- **Решение**: по умолчанию `LLM_MODE=template`, `IMAGE_MODE=pillow`.
- **Причина**: демо должно работать без внешних сервисов/ключей.
- **Следствие**: всегда есть fallback, даже если API недоступно.

## 2) GigaChat интеграция как опциональный провайдер

- **Решение**: `LLM_MODE=gigachat` и `IMAGE_MODE=gigachat`, клиент + провайдеры выделены отдельными модулями.
- **Причина**: удобная смена провайдеров, изоляция авторизации/скачивания изображений, тестируемость.
- **Файлы**: `backend/app/agent/gigachat_client.py`, `backend/app/agent/gigachat_providers.py`.

## 3) Строгий формат ответа LLM для текста

- **Решение**: просим **строго JSON** `{tone, subject, body}` и валидируем.
- **Причина**: снижает галлюцинации и упрощает автоматизацию.
- **Файлы**: `backend/app/agent/llm_prompts.py`, `backend/app/agent/llm_provider.py`.
- **Промпты для персонализации**: 
  - Детальные инструкции по персонализации с использованием FACTS (имя, компания, должность)
  - Универсальные промпты, адаптирующиеся под разные типы праздников (birthday, holiday)
  - Рекомендации по тону на основе сегмента клиента и tone_hint из holiday_tags
  - Требования к длине body: 450-1200 символов (целевой диапазон 600-900) для более содержательных текстов
  - Акцент на разнообразие формулировок и естественность текста
  - **Практика**: некоторые провайдеры (в т.ч. GigaChat) могут вернуть «почти JSON» с **неэкранированными переносами строк внутри строк**.  
    В `parse_llm_json()` есть безопасный repair: переносы строк **внутри** строковых литералов экранируются как `\\n`, после чего JSON парсится.
  - **Важно про “обрывки” в логах**: предупреждения печатают только **preview** первых ~500 символов ответа для читабельности логов.  
    В БД/в outbox сохраняется **полный** текст `Greeting.body`.

## 4) Изображения через встроенную text2image (function_call="auto")

- **Решение**: для картинок используем `function_call="auto"` и парсим `<img src="file_id">`.
- **Причина**: соответствует официальной схеме из документации.
- **Файлы**: `backend/app/agent/gigachat_client.py` (extract + download), `backend/app/agent/gigachat_providers.py`.
- **Промпт**: используется прямая команда "Нарисуй ..." как в официальных примерах GigaChat, промпт максимально простой для надежной генерации.

## 5) Idempotency на доставку

- **Решение**: `Delivery.idempotency_key` уникален; повторные запуски не создают дублей.
- **Причина**: регулярный конвейер должен быть безопасен к повторным прогонам.
- **Файлы**: `backend/app/services/sender.py`.

## 6) Runtime‑данные не в git

- **Решение**: `backend/data/` и `backend/.env` игнорируются.
- **Причина**: безопасность (секреты/артефакты/БД) и чистота репозитория.
- **Файлы**: `.gitignore`, `SECURITY.md`.

## 7) Windows‑friendly запуск

- **Решение**: `scripts/run_backend.cmd` с автоподбором порта.
- **Причина**: Windows часто имеет ограничения/занятые порты (WinError 10013/“залипшие” процессы).
- **Файлы**: `scripts/run_backend.cmd`, `backend/app/worker/run_dev_server.py`, `scripts/kill_port.cmd`.

## 8) Lifespan вместо on_event

- **Решение**: FastAPI startup реализован через `lifespan`.
- **Причина**: убрать deprecation warnings и быть совместимыми с будущими версиями.
- **Файлы**: `backend/app/main.py`.

## 9) VIP approval gating

- **Решение**: для клиентов с `segment=vip` агент создаёт `Greeting.status="needs_approval"` и **не отправляет автоматически**.
  Отправка происходит по расписанию (в день события) после действия **Approve** в UI (через `services/approval.py`).
- **Причина**: контроль качества/рисков для VIP и соответствие требованиям процесса.
- **Файлы**: `backend/app/agent/orchestrator.py`, `backend/app/services/approval.py`, `backend/app/web/templates/greetings.html`.

## 10) Аудит запусков агента (AgentRun)

- **Решение**: каждый вызов `run_once()` создаёт запись `AgentRun` и заполняет счётчики/статус по завершению.
- **Причина**: наблюдаемость конвейера, демо “регулярности”, диагностика ошибок и объёма работы.
- **Файлы**: `backend/app/db/models.py` (AgentRun), `backend/app/agent/orchestrator.py`, UI: `backend/app/web/router.py` + `backend/app/web/templates/runs.html`.

## 11) Лимит получателей на праздники (демо‑контроль токенов)

- **Решение**: при генерации holiday‑ивентов ограничиваем число получателей (по умолчанию `MAX_HOLIDAY_RECIPIENTS=12`).
- **Причина**: праздник *для каждого клиента* быстро сжигает токены/время на демо.
- **Файлы**: `backend/app/services/event_detector.py`, `backend/app/core/config.py`, `backend/env.example`.

## 12) Reset runtime data для чистых прогонов

- **Решение**: кнопка в UI очищает runtime‑данные (Events/Greetings/Deliveries/AgentRuns) и outbox/cards/smoke артефакты, но сохраняет Clients/Holidays.
- **Причина**: повторные прогоны по умолчанию идемпотентны → много `skipped` и “старые” статусы. Reset делает демо воспроизводимым.
- **Файлы**: `backend/app/services/reset_runtime.py`, `backend/app/web/router.py`, `backend/app/web/templates/base.html`.

## 13) Скорость: лимит GigaChat-изображений за прогон

- **Решение**: ограничиваем количество генераций изображений через GigaChat за один `run_once()` (`MAX_GIGACHAT_IMAGES_PER_RUN`, по умолчанию 5). Остальные изображения — быстрый Pillow fallback.
- **Практическая настройка**: для image-generation используется отдельный `GIGACHAT_IMAGE_GENERATION_TIMEOUT_SEC`, потому что запросы на картинку стабильно медленнее обычного текста.
- **Причина**: генерация картинок самая медленная и “дорогая” по токенам/времени, особенно при нескольких событиях.
- **Файлы**: `backend/app/core/config.py`, `backend/app/agent/orchestrator.py`, `backend/env.example`.

## 14) Company enrichment через локальный demo-registry

- **Решение**: организационный профиль клиента расширен полями `inn`, `ogrn`, `kpp`, `official_company_name`, `ceo_name`, `okved_code`, `okved_name`, `company_status`, `company_address`, `company_site`, `source_url`, `enrichment_status`, `enrichment_error`, `enriched_at`.
  Enrichment работает через провайдерный слой: `demo`, `dadata` или `hybrid`, а локальные данные вынесены в `backend/app/resources/company_data/`.
- **Причина**: нужен реально работающий enrichment-контур уже сейчас, но с понятным путём к реальному внешнему источнику по ИНН без переписывания UI/API.
- **Файлы**: `backend/app/services/company_enrichment.py`, `backend/app/services/dadata_client.py`, `backend/app/resources/company_data/*`, `backend/app/db/models.py`, `backend/app/web/templates/clients.html`.

## 15) Импорт условной базы компаний из CSV

- **Решение**: CSV-справочник компаний хранится внутри `backend/app/resources/company_data/`, импортируется через отдельный сервис и upsert-логикой по `ИНН`.
- **Причина**: корень репозитория не должен играть роль “склада данных”; импорт должен быть повторяемым, понятным и управляемым через UI/API.
- **Файлы**: `backend/app/services/company_import.py`, `backend/app/resources/company_data/export-base_demo_takbup.csv`, `backend/app/web/router.py`, `backend/app/api/routes/clients.py`.

## 16) Feedback loop для Human-in-the-Loop

- **Решение**: менеджер может сохранить `score/outcome/notes` для каждого поздравления; feedback хранится в таблице `Feedback`, доступен через UI и API.
- **Причина**: без операторской оценки невозможно показать “улучшение качества” и невозможно собирать сигналы для будущего ранжирования/обучения.
- **Файлы**: `backend/app/services/feedback.py`, `backend/app/api/routes/feedback.py`, `backend/app/web/router.py`, `backend/app/web/templates/greetings.html`.

## 17) Управляемый режим отправки через `.env`

- **Решение**: время отправки вынесено в `DELIVERY_SCHEDULE_MODE` с режимами `event_date` и `immediate`; логика учитывается и при обычной отправке, и при VIP approve.
- **Причина**: демо-сценарий и реальный сценарий доставки требуют разного поведения, и это должно включаться конфигом, а не “временными if-ами”.
- **Файлы**: `backend/app/core/config.py`, `backend/app/services/due_sender.py`, `backend/app/services/approval.py`, `backend/env.example`.

## 18) Ручные события для реальной клиентской базы

- **Решение**: добавлен управляемый сценарий ручных событий: оператор может создать единичный повод для конкретного клиента или быстро подготовить demo-кампанию для нескольких реальных клиентов из импортированной базы.
- **Причина**: реальные клиенты не обязаны иметь день рождения или релевантный праздник в окне `LOOKAHEAD_DAYS`, а демонстрация должна позволять запускать генерацию по импортированной базе уже сейчас.
- **Файлы**: `backend/app/services/manual_events.py`, `backend/app/api/routes/events.py`, `backend/app/web/router.py`, `backend/app/web/templates/events.html`.

## 19) Run-level аудит результатов генерации

- **Решение**: каждое созданное агентом поздравление получает ссылку на `AgentRun`, а в UI появилась детальная страница запуска `/runs/{id}` со списком созданных поздравлений, их статусами, доставками и feedback.
- **Причина**: для демонстрации и диагностики недостаточно общих счётчиков `AgentRun`; нужно прозрачно показывать, что именно сделал конкретный прогон и каков дальнейший результат по его объектам.
- **Файлы**: `backend/app/db/models.py`, `backend/app/db/init_db.py`, `backend/app/agent/orchestrator.py`, `backend/app/web/router.py`, `backend/app/web/templates/runs.html`, `backend/app/web/templates/run_detail.html`.

## 20) Post-generation funnel на dashboard

- **Решение**: главная страница считает и показывает операционную воронку `generated -> needs approval -> delivered -> feedback`, а также ключевые health-метрики (`delivery errors`, `runs with issues`, `avg feedback score`).
- **Причина**: для презентации нужен не только “журнал сущностей”, но и один экран, который быстро объясняет качество работы конвейера после запуска агента.
- **Файлы**: `backend/app/web/router.py`, `backend/app/web/templates/dashboard.html`, `backend/tests/test_web_ui_pages.py`.

## 21) Holiday knowledge layer для генерации вне ДР

- **Решение**: встроенные календарные и профессиональные поводы вынесены в единый каталог с семантическими тегами (`category`, `focus_hint`, `prompt_hint`, `audience`), а эти теги передаются дальше в fallback и LLM-prompts.
- **Причина**: одной даты и названия праздника недостаточно, если нужно масштабировать генерацию на разные сценарии, а не только на день рождения.
- **Файлы**: `backend/app/services/holiday_catalog.py`, `backend/app/services/event_detector.py`, `backend/app/agent/generator.py`, `backend/app/agent/llm_prompts.py`, `backend/app/agent/text_generator.py`.

## 22) Общий semantic-layer для prompt-building

- **Решение**: добавлен единый слой `EventSemantics`, который собирает категорию, смысловой фокус, prompt_hint, guidance для текста и visual_theme для любого события (`birthday`, `holiday`, `manual`) и используется и в текстовой, и в image-генерации.
- **Причина**: проект не должен эволюционировать через ручное добавление “ещё одного промпта на ещё один праздник”; масштабируемее строить генерацию через семантику повода и структурированные правила.
- **Файлы**: `backend/app/agent/event_semantics.py`, `backend/app/agent/generator.py`, `backend/app/agent/llm_prompts.py`, `backend/app/agent/text_generator.py`, `backend/app/agent/gigachat_providers.py`.


