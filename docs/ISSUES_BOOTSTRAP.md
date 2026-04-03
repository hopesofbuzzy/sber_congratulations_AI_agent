# Issues Bootstrap

Готовый стартовый набор `GitHub Issues`, с которого команда может начать нормальную совместную работу.

Как использовать:
1. Открыть `Issues` в GitHub.
2. Создать issue с названием и телом ниже.
3. Назначить ответственного.
4. При необходимости поставить labels:
   - `backend`
   - `agent`
   - `web`
   - `data`
   - `qa`
   - `docs`
   - `demo`
   - `high-priority`

## Issue 1

### Title
`Организовать командный workflow через GitHub и feature-ветки`

### Body
**Зачем**

Сейчас проект уже можно делить на параллельную командную работу, но без общего workflow команда быстро упрётся в хаос по веткам, задачам и merge.

**Что сделать**

- Зафиксировать `main` как стабильную ветку.
- Начать работать только через feature-ветки.
- Завести минимальный board со статусами:
  - `Todo`
  - `In Progress`
  - `Review`
  - `Done`
- Договориться, что одна задача = одна ветка = один PR.
- Использовать `docs/TEAM_WORKFLOW.md` как базовый регламент.

**Definition of Done**

- В GitHub создан хотя бы минимальный board.
- У команды есть единый понятный регламент.
- Новые задачи дальше создаются уже по этой схеме.

**Ответственный**

DevOps/QA или backend-интегратор.

---

## Issue 2

### Title
`Усилить backend-контур доставки, статусов и run lifecycle`

### Body
**Зачем**

Сейчас MVP уже рабочий, но backend-часть должна дальше развиваться как устойчивый контур: статусы, отправка, approve, fallback, run-level аудит.

**Что сделать**

- Проверить целостность жизненного цикла `Greeting`:
  - `generated`
  - `needs_approval`
  - `approved`
  - `sent`
  - `skipped`
  - `error`
- Усилить контроль сценариев доставки:
  - SMTP
  - file fallback
  - отсутствие email
  - allowlist / test recipients
- Проверить согласованность `AgentRun -> Greeting -> Delivery`.
- Выделить всё, что связано с delivery safety, в понятный и поддерживаемый контур.

**Основные файлы**

- `backend/app/db/*`
- `backend/app/services/sender.py`
- `backend/app/services/due_sender.py`
- `backend/app/services/approval.py`
- `backend/app/agent/orchestrator.py`

**Definition of Done**

- Жизненный цикл delivery понятен и не разваливается на demo/real сценариях.
- Ключевые статусы покрыты тестами.
- Нет неоднозначного поведения при fallback-сценариях.

**Ответственный**

Backend/DB инженер.

---

## Issue 3

### Title
`Улучшить AI-контур генерации текста и картинок без потери demo-stability`

### Body
**Зачем**

Сейчас контур генерации уже работает, но именно здесь будет основное развитие качества: тексты, image prompts, fallback, prompt-building.

**Что сделать**

- Дальше стабилизировать JSON-ответ GigaChat.
- Усилить prompt-building без превращения его в набор случайных `if`.
- Развивать event-specific image presets:
  - `birthday`
  - `Новый год`
  - `8 Марта`
  - business/manual
- Сохранить строгие запреты:
  - без людей
  - без текста
  - без хаотичных сцен
- Отдельно проработать quality path для fallback generation.

**Основные файлы**

- `backend/app/agent/*`

**Definition of Done**

- Контур генерации даёт более предсказуемый результат.
- Нет ухудшения demo-stability.
- Новые правила покрыты тестами.

**Ответственный**

AI/Agent инженер.

---

## Issue 4

### Title
`Довести Web/UI и demo-flow до командно поддерживаемого состояния`

### Body
**Зачем**

Интерфейс уже пригоден для демонстрации, но дальше его нужно развивать как рабочее операторское место, а не как набор разрозненных страниц.

**Что сделать**

- Проверить сценарий:
  - `Seed`
  - `Enrich`
  - `Events`
  - `Run agent`
  - `Greetings`
  - `Runs`
  - `Deliveries`
- Упростить всё, что мешает демо:
  - длинные формы
  - непонятные статусы
  - перегруженные таблицы
- Улучшить связность страниц между собой.
- Поддерживать единый presentation-ready стиль.

**Основные файлы**

- `backend/app/web/router.py`
- `backend/app/web/templates/*`

**Definition of Done**

- Demo-flow проходится без путаницы.
- UI можно поддерживать параллельно без ломания общего сценария.
- Новые страницы и действия не выбиваются из общего UX.

**Ответственный**

Web/UX инженер.

---

## Issue 5

### Title
`Развить слой данных: import, enrichment, holidays, manual events`

### Body
**Зачем**

Качество генерации напрямую зависит от качества входных данных. Эта часть должна развиваться как отдельная подсистема.

**Что сделать**

- Продолжить улучшение CSV-импорта.
- Усилить `DaData`-контур и обработку enrichment-ошибок.
- Развивать knowledge layer праздников.
- Поддерживать manual events как управляемый путь в генерацию.
- Улучшать нормализацию `segment/profession/business-context`.

**Основные файлы**

- `backend/app/services/company_*`
- `backend/app/services/dadata_client.py`
- `backend/app/services/holiday_catalog.py`
- `backend/app/services/event_detector.py`
- `backend/app/services/manual_events.py`
- `backend/app/resources/*`

**Definition of Done**

- Импорт и enrichment остаются предсказуемыми.
- Новые поводы и данные подключаются без архитектурного хаоса.
- Генерация получает более качественный фактологический контекст.

**Ответственный**

Data/Enrichment инженер.

---

## Issue 6

### Title
`Поддерживать demo-ready качество через тесты, документацию и CI`

### Body
**Зачем**

Проект уже вышел из стадии “локального прототипа” и должен дальше развиваться без потери воспроизводимости и понятности.

**Что сделать**

- Следить, чтобы каждый значимый блок имел:
  - тесты
  - docs
  - проверяемый сценарий
- Держать в порядке:
  - `README.md`
  - `docs/DECISIONS.md`
  - `docs/PROJECT_OVERVIEW.md`
  - `docs/TEAM_WORKFLOW.md`
  - `ROADMAP.md`
  - `backend/env.example`
- Поддерживать CI как минимальный quality gate:
  - `pytest`
  - `ruff`
  - `black --check`

**Основные файлы**

- `backend/tests/*`
- `.github/workflows/*`
- `docs/*`
- `README.md`
- `backend/env.example`

**Definition of Done**

- Любой новый важный блок сопровождается проверкой и документацией.
- Репозиторий остаётся понятным для нового участника.
- Demo-ready состояние не деградирует со временем.

**Ответственный**

DevOps/QA инженер.

---

## Рекомендуемый порядок запуска

Если создавать не всё сразу, а по уму, то лучше так:

1. `Организовать командный workflow через GitHub и feature-ветки`
2. `Поддерживать demo-ready качество через тесты, документацию и CI`
3. Остальные 4 role-based issue по подсистемам

## Если захотите сделать ещё профессиональнее

Можно потом добавить:
- шаблон issue;
- шаблон PR;
- labels;
- simple project board;
- CODEOWNERS по подсистемам.
