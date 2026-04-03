# Анализ источников данных и архитектуры подключения каналов

## 📋 Резюме

**Главный вывод:** Архитектура системы **частично готова** к подключению собственных каналов данных, но имеет **критические ограничения** для полноценной интеграции с внешними источниками в реальном времени. Текущая реализация ориентирована на статические CSV-файлы и демо-реестры, а не на динамические API и потоковые данные.

**Оценка гибкости архитектуры:** ~45%  
**Оценка готовности к production-интеграциям:** ~30%

---

## 🔍 1. Источники данных для поздравлений: текущее состояние

### 1.1. Основные источники данных

Система использует **три основных источника** данных о клиентах и компаниях:

#### Источник 1: Локальный CSV-файл (основной для демо)
**Файл:** `backend/app/resources/company_data/export-base_demo_takbup.csv`  
**Структура:** 34 колонки с данными о компаниях

```csv
"Название компании";"ИНН";"ОГРН";"Руководитель (по ЕГРЮЛ)";"Рубрика";"Подрубрика";
"Главный ОКВЭД (код)";"Главный ОКВЭД (название)";"Численность сотрудников (чел.) *";
"Выручка (тыс. руб.) *";"Email компании";"Мобильный телефон компании";...
```

**Доказательства использования:**

**Файл:** `backend/app/services/company_import.py`  
**Строки:** 99-107 (определение пути к CSV)

```python
def _csv_path() -> Path:
    raw = (settings.company_import_csv_path or "").strip()
    if not raw:
        return DEFAULT_COMPANY_IMPORT_CSV_PATH  # ← Жёстко заданный путь
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / raw
    return path
```

**Строки:** 154-237 (импорт из CSV)

```python
async def import_clients_from_company_csv(session: AsyncSession) -> dict:
    path = _csv_path()
    if not path.exists():
        raise FileNotFoundError(f"CSV-файл не найден: {path}")
    
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")  # ← Только CSV с точкой с запятой
        # ... парсинг строк
```

**Проблемы:**
- ❌ Только один формат (CSV с `;` разделителем)
- ❌ Файл должен существовать локально
- ❌ Нет поддержки Excel (`.xlsx`), JSON, XML
- ❌ Нет автоматического обновления (только ручной импорт)
- ❌ Нет валидации схемы данных

---

#### Источник 2: Демо-реестр компаний (JSON)
**Файл:** `backend/app/resources/company_data/demo_registry.json` (предположительно)  
**Использование:** fallback для enrichment

**Файл:** `backend/app/services/company_enrichment.py`  
**Строки:** 48-72 (загрузка демо-реестра)

```python
@lru_cache(maxsize=1)
def _demo_registry() -> list[CompanyProfile]:
    if not DEMO_REGISTRY_PATH.exists():
        return []
    raw_items = json.loads(DEMO_REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        CompanyProfile(
            inn=str(item["inn"]),
            official_company_name=str(item["official_company_name"]),
            ceo_name=item.get("ceo_name"),
            okved_code=item.get("okved_code"),
            # ... остальные поля
        )
        for item in raw_items
    ]
```

**Строки:** 75-89 (поиск по ИНН или названию)

```python
def lookup_demo_company_profile(
    *, inn: str | None, company_name: str | None
) -> CompanyProfile | None:
    norm_inn = re.sub(r"\D", "", inn or "")
    norm_company = _normalize_name(company_name)
    for item in _demo_registry():
        if norm_inn and item.inn == norm_inn:
            return item
        # ... поиск по названию
    return None
```

**Проблемы:**
- ❌ Статичные данные (не обновляются)
- ❌ Ограниченный набор компаний (только демо)
- ❌ Нет механизма добавления новых компаний без изменения кода

---

#### Источник 3: DaData API (внешний сервис)
**Файл:** `backend/app/services/dadata_client.py`  
**Строки:** 22-57 (запрос к DaData)

```python
async def find_party_by_inn(inn: str) -> dict | None:
    api_key = (settings.dadata_api_key or "").strip()
    if not api_key:
        raise DadataConfigurationError("Не задан DADATA_API_KEY.")
    
    payload = {"query": inn}
    # ... настройка фильтров
    
    base_url = settings.dadata_base_url.rstrip("/")
    url = f"{base_url}/findById/party"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=settings.dadata_timeout_sec) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise DadataRequestError(f"Ошибка запроса к DaData: {exc}") from exc
    
    data = response.json()
    suggestions = data.get("suggestions") or []
    if not suggestions:
        return None
    return suggestions[0]
```

**Конфигурация:** `backend/app/core/config.py`  
**Строки:** 78-84

```python
# DaData company enrichment (optional)
dadata_api_key: str | None = None
dadata_base_url: str = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
dadata_timeout_sec: float = 10.0
dadata_party_branch_type: str = "MAIN"
dadata_party_type: str = "LEGAL"
dadata_party_status: str = "ACTIVE"
```

**Преимущества:**
- ✅ Реальное API с актуальными данными
- ✅ Настройка через environment variables
- ✅ Обработка ошибок
- ✅ Таймауты

**Проблемы:**
- ⚠️ Только один провайдер (DaData)
- ⚠️ Нет fallback на другие API (например, Контур.Фокус, СПАРК)
- ⚠️ Нет кеширования ответов (повторные запросы за одни и те же данные)
- ⚠️ Нет лимитирования запросов (risk of rate limiting)

---

### 1.2. Стратегия выбора источника (enrichment provider)

**Файл:** `backend/app/services/company_enrichment.py`  
**Строки:** 144-182 (логика выбора провайдера)

```python
async def lookup_company_profile(
    *,
    inn: str | None,
    company_name: str | None,
) -> tuple[CompanyProfile | None, str | None]:
    provider = (settings.company_enrichment_provider or "demo").strip().lower()
    if provider not in {"demo", "dadata", "hybrid"}:
        provider = "demo"
    
    if provider == "demo":
        profile = lookup_demo_company_profile(inn=inn, company_name=company_name)
        return profile, None if profile else "Организация не найдена в локальном demo-реестре."
    
    if provider == "dadata":
        try:
            profile = await lookup_dadata_company_profile(inn=inn)
        except (DadataConfigurationError, DadataRequestError) as exc:
            return None, str(exc)
        if profile is None:
            return None, "Организация не найдена в DaData по указанному ИНН."
        return profile, None
    
    # hybrid режим
    try:
        dadata_profile = await lookup_dadata_company_profile(inn=inn)
    except DadataConfigurationError:
        dadata_profile = None
    except DadataRequestError as exc:
        demo_profile = lookup_demo_company_profile(inn=inn, company_name=company_name)
        if demo_profile is not None:
            return demo_profile, None
        return None, str(exc)
    if dadata_profile is not None:
        return dadata_profile, None
    
    demo_profile = lookup_demo_company_profile(inn=inn, company_name=company_name)
    if demo_profile is not None:
        return demo_profile, None
    return None, "Организация не найдена ни в DaData, ни в локальном demo-реестре."
```

**Конфигурация:** `backend/app/core/config.py`  
**Строка:** 27

```python
company_enrichment_provider: str = "demo"  # demo|dadata|hybrid
```

**Анализ:**
- ✅ Есть переключение между провайдерами
- ✅ Есть гибридный режим (fallback)
- ❌ Нет поддержки более 2 провайдеров одновременно
- ❌ Нет динамического выбора (только статическая настройка)
- ❌ Нет приоритизации по качеству данных

---

## 🔌 2. Возможность подключения своих каналов данных

### 2.1. Что можно подключить «как есть»

#### ✅ CSV-файлы произвольного формата
**Гибкость:** Средняя

Можно изменить структуру CSV, но потребуется правка кода:

**Файл:** `backend/app/services/company_import.py`  
**Строки:** 163-220 (парсинг CSV)

```python
with path.open("r", encoding="utf-8", newline="") as fh:
    reader = csv.DictReader(fh, delimiter=";")  # ← Можно изменить на ','
    reader.fieldnames = [_normalize_header(name) for name in (reader.fieldnames or [])]
    for row in reader:
        row = {_normalize_header(key): value for key, value in row.items()}
        company_name = _clean_cell(row.get("Название компании"))  # ← Жёсткие имена колонок
        inn = re.sub(r"\D", "", row.get("ИНН") or "")
        # ...
```

**Что нужно изменить:**
1. Заменить `delimiter=";"` на нужный разделитель
2. Изменить маппинг имён колонок (строки 168-219)
3. Добавить обработку новых форматов дат, телефонов и т.д.

**Оценка усилий:** 2-4 часа на новый формат CSV

---

#### ✅ Дополнительный API-провайдер (через доработку)
**Гибкость:** Высокая (требует доработки)

Архитектура позволяет добавить новый класс-провайдер по аналогии с `dadata_client.py`:

```python
# Пример: Kontur.Focus провайдер
class KonturClient:
    async def get_company_by_inn(self, inn: str) -> dict | None:
        api_key = settings.kontur_api_key
        url = f"{settings.kontur_base_url}/companies/{inn}"
        # ... реализация
```

**Что нужно сделать:**
1. Создать файл `backend/app/services/kontur_client.py`
2. Реализовать методы по аналогии с `dadata_client.py`
3. Добавить настройки в `config.py`
4. Обновить `lookup_company_profile()` для поддержки нового провайдера

**Оценка усилий:** 4-8 часов на один API

---

### 2.2. Что НЕЛЬЗЯ подключить без серьёзной переработки

#### ❌ Базы данных (PostgreSQL, MySQL, 1C)
**Проблема:** Отсутствует слой абстракции для SQL-источников

Сейчас данные загружаются только через CSV/API. Для подключения CRM/ERP потребуется:
- Создание новых моделей SQLAlchemy
- Реализация репозиториев для извлечения данных
- Настройка соединений с внешними БД
- Маппинг полей между системами

**Оценка усилий:** 20-40 часов

---

#### ❌ GraphQL API
**Проблема:** Используется только `httpx` для REST-запросов

Для GraphQL потребуется:
- Установка библиотеки (`gql`, `graphql-core`)
- Создание клиентов для конкретных API
- Парсинг GraphQL-схем
- Обработка subscription (для real-time)

**Оценка усилий:** 8-16 часов

---

#### ❌ Message Queues (Kafka, RabbitMQ)
**Проблема:** Отсутствует event-driven архитектура

Система работает в режиме polling (опрос по расписанию). Для работы с очередями сообщений потребуется:
- Интеграция с брокером сообщений
- Создание consumers для обработки событий
- Переход от cron к реактивной архитектуре

**Оценка усилий:** 40-80 часов (архитектурные изменения)

---

#### ❌ Webhook-и от внешних систем
**Проблема:** Нет endpoint'ов для приёма входящих событий

**Файл:** `backend/app/web/router.py` (предположительно)  
**Текущее состояние:** Нет обработчиков webhook

Для поддержки webhook потребуется:
- Создание API routes для приёма событий
- Валидация подписей (HMAC, JWT)
- Обработка различных форматов payload
- Идемпотентность обработки

**Оценка усилий:** 16-24 часа

---

## 🏗️ 3. Архитектурный анализ гибкости

### 3.1. Положительные аспекты архитектуры

#### ✅ Dependency Injection через Settings
**Файл:** `backend/app/core/config.py`

Все конфигурации вынесены в `Settings`, что позволяет:
- Менять провайдеров через `.env`
- Настраивать таймауты, URL, ключи
- Переключать режимы (demo/production)

**Пример:**
```python
# .env файл
company_enrichment_provider=dadata
dadata_api_key=your_key_here
dadata_base_url=https://suggestions.dadata.ru/suggestions/api/4_1/rs
```

---

#### ✅ Стратегия через provider pattern
**Файл:** `backend/app/services/company_enrichment.py`

Реализован паттерн Strategy для выбора источника:
```python
if provider == "demo":
    ...
elif provider == "dadata":
    ...
elif provider == "hybrid":
    ...
```

**Потенциал:** Легко добавить новые ветви для других провайдеров

---

#### ✅ Асинхронная архитектура
**Файл:** `backend/app/services/dadata_client.py`

Использование `async/await` позволяет:
- Параллелить запросы к разным API
- Не блокировать поток ввода-вывода
- Масштабироваться на большие объёмы данных

**Пример:**
```python
async with httpx.AsyncClient(timeout=settings.dadata_timeout_sec) as client:
    response = await client.post(url, headers=headers, json=payload)
```

---

### 3.2. Критические архитектурные ограничения

#### ❌ Монолитный service layer
**Проблема:** Логика импорта, enrichment и отправки смешана в одном слое

**Файл:** `backend/app/services/company_import.py` (238 строк)  
**Файл:** `backend/app/services/company_enrichment.py` (258 строк)

Отсутствует разделение на:
- Data Sources (абстрактный слой источников)
- Parsers (парсеры форматов)
- Repositories (репозитории для доступа к данным)
- Services (бизнес-логика)

**Последствия:**
- Трудно тестировать отдельные компоненты
- Сложно добавлять новые источники без модификации существующего кода
- Нарушен принцип Single Responsibility

---

#### ❌ Жёсткий маппинг полей
**Проблема:** Имена колонок CSV захардкожены в коде

**Файл:** `backend/app/services/company_import.py`  
**Строки:** 168-219

```python
company_name = _clean_cell(row.get("Название компании"))
inn = re.sub(r"\D", "", row.get("ИНН") or "")
ogrn = re.sub(r"\D", "", row.get("ОГРН") or "")
ceo_name = _clean_cell(row.get("Руководитель (по ЕГРЮЛ)"))
okved_code = _clean_cell(row.get("Главный ОКВЭД (код)"))
```

**Последствия:**
- Нельзя использовать CSV с другими именами колонок
- Требуется правка кода для каждого нового формата
- Нет конфигурационного файла для маппинга

**Как должно быть:**
```python
# config/mapping.yaml
csv_field_mapping:
  company_name_variants: ["Название компании", "Organization Name", "Firma"]
  inn_variants: ["ИНН", "INN", "Tax ID"]
  
# code
mapping = load_field_mapping()
company_name = _clean_cell(row.get(find_matching_key(row, mapping['company_name_variants'])))
```

---

#### ❌ Отсутствие валидации данных на входе
**Проблема:** Нет схемы валидации для импортируемых данных

**Файл:** `backend/app/services/company_import.py`  
**Строки:** 163-170

```python
for row in reader:
    row = {_normalize_header(key): value for key, value in row.items()}
    company_name = _clean_cell(row.get("Название компании"))
    inn = re.sub(r"\D", "", row.get("ИНН") or "")
    if not company_name or not inn:  # ← Единственная валидация
        skipped += 1
        continue
```

**Последствия:**
- Некорректные данные могут попасть в базу
- Нет информативных ошибок для пользователя
- Нет отчёта о валидации (какие строки отклонены и почему)

**Как должно быть:**
```python
from pydantic import BaseModel, validator

class CompanyImportRow(BaseModel):
    company_name: str
    inn: str
    ogrn: Optional[str]
    
    @validator('inn')
    def validate_inn(cls, v):
        if len(v) not in [10, 12]:
            raise ValueError('ИНН должен содержать 10 или 12 цифр')
        return v

# Использование
try:
    validated = CompanyImportRow(**row)
except ValidationError as e:
    logger.error(f"Строка {line_number} не прошла валидацию: {e}")
    skipped += 1
    continue
```

---

#### ❌ Нет кеширования внешних запросов
**Проблема:** Повторные запросы одних и тех же данных

**Файл:** `backend/app/services/dadata_client.py`  
**Отсутствует:** Кеширование ответов

При импорте 1000 компаний с повторющимися ИНН (например, филиалы) будут выполнены дублирующие запросы к API.

**Последствия:**
- Перерасход лимитов API
- Увеличение времени импорта
- Риск блокировки за частые запросы

**Как должно быть:**
```python
from functools import lru_cache
import asyncio

# Кеширование в памяти (для одного запуска)
@lru_cache(maxsize=1000)
def _cached_find_party(inn: str) -> dict | None:
    ...

# Или Redis для распределённого кеширования
async def get_cached_company(inn: str):
    cache_key = f"dadata:party:{inn}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    result = await find_party_by_inn(inn)
    if result:
        await redis.setex(cache_key, 86400, json.dumps(result))  # 24 часа
    return result
```

---

## 📊 4. Оценка по критериям гибкости

| Критерий | Оценка | Комментарий |
|----------|--------|-------------|
| **Поддержка форматов данных** | 2/5 | Только CSV + JSON (демо) |
| **Подключение новых API** | 3/5 | Требует доработки, но архитектура позволяет |
| **Конфигурируемость** | 4/5 | Хорошая работа с Settings |
| **Валидация данных** | 1/5 | Практически отсутствует |
| **Кеширование** | 1/5 | Отсутствует |
| **Обработка ошибок** | 3/5 | Базовая, нет детализации |
| **Масштабируемость** | 2/5 | Нет очереди задач, лимитирования |
| **Тестируемость** | 2/5 | Монолитные сервисы, трудно мокировать |
| **Расширяемость** | 3/5 | Можно добавить провайдеры, но с правками |
| **Документированность** | 2/5 | Нет документации по интеграциям |

**Средняя оценка гибкости:** 23/50 ≈ **46%**

---

## 🚀 5. Направления для улучшения

### Приоритет 1: Критические улучшения (быстрые победы)

#### 5.1. Конфигурационный маппинг полей CSV
**Файл для создания:** `backend/app/config/field_mapping.py`

```python
from typing import Dict, List
from pydantic import BaseModel

class CSVFieldMapping(BaseModel):
    company_name: List[str] = ["Название компании", "Organization Name", "Company"]
    inn: List[str] = ["ИНН", "INN", "Tax ID", "TIN"]
    ogrn: List[str] = ["ОГРН", "OGRN"]
    ceo_name: List[str] = ["Руководитель (по ЕГРЮЛ)", "CEO", "Director"]
    email: List[str] = ["Email компании", "Company Email", "E-mail"]
    phone: List[str] = ["Мобильный телефон компании", "Phone", "Telephone"]
    okved_code: List[str] = ["Главный ОКВЭД (код)", "OKVED Code"]
    okved_name: List[str] = ["Главный ОКВЭД (название)", "OKVED Name"]

def find_field(row: Dict[str, str], variants: List[str]) -> str | None:
    """Поиск поля по одному из вариантов имени"""
    for variant in variants:
        if variant in row:
            return row[variant]
    # Поиск case-insensitive
    row_lower = {k.lower(): v for k, v in row.items()}
    for variant in variants:
        if variant.lower() in row_lower:
            return row_lower[variant.lower()]
    return None
```

**Изменения в `company_import.py`:**
```python
from app.config.field_mapping import CSVFieldMapping, find_field

mapping = CSVFieldMapping()

for row in reader:
    company_name = _clean_cell(find_field(row, mapping.company_name))
    inn = re.sub(r"\D", "", find_field(row, mapping.inn) or "")
    # ...
```

**Выгода:** 
- Поддержка CSV с любыми именами колонок
- Без изменения кода для новых форматов
- **Оценка усилий:** 3-5 часов

---

#### 5.2. Pydantic-валидация импортируемых данных
**Файл для создания:** `backend/app/schemas/import_rows.py`

```python
from pydantic import BaseModel, Field, validator
import re

class CompanyImportRow(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    inn: str
    ogrn: str | None = None
    ceo_name: str | None = None
    email: str | None = None
    phone: str | None = None
    okved_code: str | None = None
    
    @validator('inn')
    def validate_inn(cls, v):
        clean_inn = re.sub(r'\D', '', v)
        if len(clean_inn) not in [10, 12]:
            raise ValueError('ИНН должен содержать 10 или 12 цифр')
        return clean_inn
    
    @validator('ogrn')
    def validate_ogrn(cls, v):
        if v:
            clean_ogrn = re.sub(r'\D', '', v)
            if len(clean_ogrn) != 13:
                raise ValueError('ОГРН должен содержать 13 цифр')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Некорректный email')
        return v
```

**Выгода:**
- Автоматическая валидация перед сохранением
- Информативные ошибки
- **Оценка усилий:** 4-6 часов

---

#### 5.3. Кеширование запросов к внешним API
**Файл для изменения:** `backend/app/services/dadata_client.py`

```python
from functools import lru_cache
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("./data/cache/dadata")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _get_cache_key(inn: str) -> str:
    return hashlib.md5(f"inn:{inn}".encode()).hexdigest()

def _load_from_cache(inn: str) -> dict | None:
    cache_file = CACHE_DIR / f"{_get_cache_key(inn)}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None

def _save_to_cache(inn: str, data: dict):
    cache_file = CACHE_DIR / f"{_get_cache_key(inn)}.json"
    cache_file.write_text(json.dumps(data))

async def find_party_by_inn(inn: str) -> dict | None:
    # Проверка кеша
    cached = _load_from_cache(inn)
    if cached:
        return cached
    
    # ... существующий код запроса ...
    
    # Сохранение в кеш
    if result:
        _save_to_cache(inn, result)
    
    return result
```

**Выгода:**
- Снижение нагрузки на API
- Ускорение повторных импортов
- **Оценка усилий:** 3-4 часа

---

### Приоритет 2: Среднесрочные улучшения

#### 5.4. Абстрактный слой DataSource
**Файл для создания:** `backend/app/data_sources/base.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any

class DataSource(ABC):
    """Абстрактный базовый класс для источников данных"""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def fetch_companies(self, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """Потоковое получение компаний"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Проверка доступности источника"""
        pass
```

**Файл для создания:** `backend/app/data_sources/csv_source.py`

```python
from app.data_sources.base import DataSource

class CSVDataSource(DataSource):
    def __init__(self, file_path: str, delimiter: str = ";"):
        self.file_path = file_path
        self.delimiter = delimiter
        self.file_handle = None
    
    async def connect(self) -> None:
        self.file_handle = open(self.file_path, "r", encoding="utf-8")
    
    async def disconnect(self) -> None:
        if self.file_handle:
            self.file_handle.close()
    
    async def fetch_companies(self, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        import csv
        reader = csv.DictReader(self.file_handle, delimiter=self.delimiter)
        for row in reader:
            yield row
```

**Файл для создания:** `backend/app/data_sources/api_source.py`

```python
from app.data_sources.base import DataSource

class APIDataSource(DataSource):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = None
    
    async def connect(self) -> None:
        import httpx
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
    
    async def fetch_companies(self, inn_list: list[str]) -> AsyncIterator[Dict[str, Any]]:
        for inn in inn_list:
            response = await self.client.get(f"/companies/{inn}")
            response.raise_for_status()
            yield response.json()
```

**Выгода:**
- Единый интерфейс для всех источников
- Легко добавлять новые источники
- Упрощение тестирования (моки)
- **Оценка усилий:** 12-16 часов

---

#### 5.5. Factory для создания DataSource
**Файл для создания:** `backend/app/data_sources/factory.py`

```python
from typing import Type
from app.data_sources.base import DataSource
from app.data_sources.csv_source import CSVDataSource
from app.data_sources.api_source import APIDataSource
from app.data_sources.database_source import DatabaseDataSource

class DataSourceFactory:
    _registry: Dict[str, Type[DataSource]] = {
        "csv": CSVDataSource,
        "api": APIDataSource,
        "database": DatabaseDataSource,
    }
    
    @classmethod
    def register(cls, name: str, source_class: Type[DataSource]):
        cls._registry[name] = source_class
    
    @classmethod
    def create(cls, source_type: str, **config) -> DataSource:
        if source_type not in cls._registry:
            raise ValueError(f"Unknown data source type: {source_type}")
        return cls._registry[source_type](**config)
```

**Использование:**
```python
# Через конфиг
source = DataSourceFactory.create(
    source_type=settings.data_source_type,  # "csv", "api", "database"
    file_path=settings.csv_file_path,
    base_url=settings.api_base_url,
    # ...
)
```

**Выгода:**
- Динамический выбор источника через конфиг
- Расширение без изменения существующего кода (Open/Closed Principle)
- **Оценка усилий:** 4-6 часов

---

#### 5.6. Поддержка нескольких источников одновременно
**Файл для создания:** `backend/app/data_sources/aggregator.py`

```python
from typing import List, AsyncIterator
from app.data_sources.base import DataSource

class DataSourceAggregator:
    """Агрегатор для работы с несколькими источниками"""
    
    def __init__(self, sources: List[DataSource], strategy: str = "merge"):
        self.sources = sources
        self.strategy = strategy  # "merge", "priority", "fallback"
    
    async def fetch_all(self) -> AsyncIterator[Dict[str, Any]]:
        seen_inns = set()
        
        for source in self.sources:
            async for company in source.fetch_companies():
                inn = company.get('inn')
                
                if self.strategy == "merge":
                    if inn not in seen_inns:
                        yield company
                        seen_inns.add(inn)
                
                elif self.strategy == "priority":
                    # Первый источник имеет приоритет
                    if inn not in seen_inns:
                        yield company
                        seen_inns.add(inn)
                
                elif self.strategy == "fallback":
                    # Используются все источники, даже с дубликатами
                    yield company
```

**Выгода:**
- Комбинирование данных из разных источников
- Гибкие стратегии слияния
- **Оценка усилий:** 6-8 часов

---

### Приоритет 3: Долгосрочные архитектурные изменения

#### 5.7. Event-driven архитектура для real-time данных
**Требуемые изменения:**
- Интеграция с message broker (RabbitMQ/Kafka)
- Создание consumers для обработки событий
- Переход от cron к реактивной модели

**Файл для создания:** `backend/app/events/consumer.py`

```python
import asyncio
from aiormq import connect, Connection
from app.services.greeting_generator import generate_greeting

class EventConsumer:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Connection | None = None
    
    async def connect(self):
        self.connection = await connect(self.rabbitmq_url)
    
    async def start_consuming(self):
        channel = await self.connection.channel()
        queue = await channel.queue_declare("greeting_events")
        
        async with channel.Processor(queue) as processor:
            async for message in processor:
                await self.handle_event(message.body)
                await message.ack()
    
    async def handle_event(self, event_body: bytes):
        event = json.loads(event_body)
        
        if event['type'] == 'client_birthday':
            await generate_greeting(client_id=event['client_id'], event_type='birthday')
        elif event['type'] == 'company_anniversary']:
            await generate_greeting(client_id=event['client_id'], event_type='anniversary')
        elif event['type'] == 'state_award':
            await generate_greeting(client_id=event['client_id'], event_type='award')
```

**Выгода:**
- Обработка событий в реальном времени
- Масштабируемость
- Интеграция с внешними системами
- **Оценка усилий:** 40-60 часов

---

#### 5.8. GraphQL слой для гибких запросов
**Файл для создания:** `backend/app/graphql/schema.py`

```python
import strawberry
from typing import List, Optional

@strawberry.type
class Company:
    inn: str
    name: str
    ceo_name: Optional[str]
    okved_code: Optional[str]
    employees: Optional[int]

@strawberry.type
class Query:
    @strawberry.field
    async def companies(self, inn_list: List[str]) -> List[Company]:
        # Гибкий запрос к нескольким источникам
        ...
    
    @strawberry.field
    async def upcoming_events(self, days: int = 7) -> List[Event]:
        # Получение событий на период
        ...
```

**Выгода:**
- Клиенты запрашивают только нужные поля
- Снижение нагрузки на сеть
- Гибкость интеграций
- **Оценка усилий:** 20-30 часов

---

## 📈 6. Roadmap улучшений

### Этап 1: Быстрые победы (1-2 недели)
1. ✅ Конфигурационный маппинг полей CSV (3-5 часов)
2. ✅ Pydantic-валидация данных (4-6 часов)
3. ✅ Кеширование API-запросов (3-4 часа)
4. ✅ Документация по подключению источников (4-6 часов)

**Итого:** 14-21 час  
**Результат:** Поддержка произвольных CSV, валидация, ускорение импорта

---

### Этап 2: Архитектурные улучшения (3-4 недели)
1. ✅ Абстрактный слой DataSource (12-16 часов)
2. ✅ Factory для источников (4-6 часов)
3. ✅ Агрегатор источников (6-8 часов)
4. ✅ Поддержка Excel/JSON форматов (8-12 часов)
5. ✅ Rate limiting для API (4-6 часов)

**Итого:** 34-48 часов  
**Результат:** Модульная архитектура, поддержка множественных источников

---

### Этап 3: Production-ready (2-3 месяца)
1. ⚠️ Event-driven архитектура (40-60 часов)
2. ⚠️ GraphQL API (20-30 часов)
3. ⚠️ Интеграция с популярными CRM (1C, Bitrix24, amoCRM) (40-60 часов)
4. ⚠️ Мониторинг и алертинг (16-24 часа)
5. ⚠️ Распределённое кеширование (Redis) (12-16 часов)

**Итого:** 128-190 часов  
**Результат:** Полноценная enterprise-система с real-time интеграциями

---

## 🎯 7. Выводы

### Текущее состояние:
- **Источники данных:** 2 (CSV + DaData API)
- **Гибкость подключения:** Низкая (требует правки кода)
- **Валидация:** Отсутствует
- **Кеширование:** Отсутствует
- **Масштабируемость:** Ограничена

### Потенциал:
- ✅ Архитектура позволяет добавлять новые API-провайдеры
- ✅ Конфигурация через Settings упрощает настройку
- ✅ Асинхронность готова к масштабированию

### Критические пробелы:
- ❌ Нет абстрактного слоя для источников данных
- ❌ Жёсткий маппинг полей CSV
- ❌ Отсутствует валидация входных данных
- ❌ Нет кеширования внешних запросов
- ❌ Отсутствует поддержка real-time событий

### Рекомендация:
Для production-развёртывания **необходимо** реализовать Этап 1 и Этап 2 roadmap (общая оценка ~50 часов). Это повысит гибкость архитектуры с 45% до 80%+ и позволит подключать собственные каналы данных без модификации кода.
