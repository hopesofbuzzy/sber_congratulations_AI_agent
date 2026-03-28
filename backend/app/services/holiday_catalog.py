from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class HolidayRule:
    month: int
    day: int
    title: str
    tags: dict


_GENERAL_HOLIDAYS: tuple[HolidayRule, ...] = (
    HolidayRule(
        1,
        1,
        "Новый год",
        {
            "type": "holiday",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "seasonal",
            "focus_hint": "renewal",
            "audience": "all",
            "prompt_hint": "Обновление, новые возможности, уверенный старт года",
        },
    ),
    HolidayRule(
        2,
        23,
        "23 Февраля",
        {
            "type": "holiday",
            "tone_hint": "official",
            "source": "builtin",
            "category": "national",
            "focus_hint": "respect",
            "audience": "all",
            "prompt_hint": "Надёжность, сила характера, уверенные решения",
        },
    ),
    HolidayRule(
        3,
        8,
        "8 Марта",
        {
            "type": "holiday",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "seasonal",
            "focus_hint": "care",
            "audience": "all",
            "prompt_hint": "Тепло, вдохновение, уважение и благодарность",
        },
    ),
    HolidayRule(
        5,
        1,
        "1 Мая",
        {
            "type": "holiday",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "seasonal",
            "focus_hint": "team",
            "audience": "all",
            "prompt_hint": "Энергия, командная работа, движение вперёд",
        },
    ),
    HolidayRule(
        5,
        9,
        "9 Мая",
        {
            "type": "holiday",
            "tone_hint": "official",
            "source": "builtin",
            "category": "national",
            "focus_hint": "gratitude",
            "audience": "all",
            "prompt_hint": "Память, уважение, благодарность, достоинство",
        },
    ),
    HolidayRule(
        5,
        26,
        "День российского предпринимательства",
        {
            "type": "holiday",
            "tone_hint": "official",
            "source": "builtin",
            "category": "business",
            "focus_hint": "growth",
            "audience": "business",
            "prompt_hint": "Предпринимательская энергия, развитие бизнеса, новые возможности",
        },
    ),
    HolidayRule(
        6,
        12,
        "День России",
        {
            "type": "holiday",
            "tone_hint": "official",
            "source": "builtin",
            "category": "national",
            "focus_hint": "stability",
            "audience": "all",
            "prompt_hint": "Устойчивость, уверенность, развитие, надёжность",
        },
    ),
    HolidayRule(
        11,
        4,
        "День народного единства",
        {
            "type": "holiday",
            "tone_hint": "official",
            "source": "builtin",
            "category": "national",
            "focus_hint": "team",
            "audience": "all",
            "prompt_hint": "Командность, единство, совместное движение к результату",
        },
    ),
    HolidayRule(
        12,
        31,
        "С наступающим Новым годом!",
        {
            "type": "holiday",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "seasonal",
            "focus_hint": "renewal",
            "audience": "all",
            "prompt_hint": "Итоги года, благодарность, ожидание сильного нового этапа",
        },
    ),
)


def _programmer_day(year: int) -> dt.date:
    return dt.date(year, 1, 1) + dt.timedelta(days=255)


_PROFESSIONAL_HOLIDAYS: dict[str, HolidayRule] = {
    "accounting": HolidayRule(
        11,
        21,
        "День бухгалтера",
        {
            "type": "professional",
            "profession": "accounting",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "stability",
            "audience": "role-based",
            "prompt_hint": "Точность, надёжность, устойчивость финансовых процессов",
        },
    ),
    "it": HolidayRule(
        0,
        0,
        "День программиста",
        {
            "type": "professional",
            "profession": "it",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "technology",
            "audience": "role-based",
            "prompt_hint": "Технологии, развитие, гибкость мышления, новые решения",
        },
    ),
    "hr": HolidayRule(
        5,
        24,
        "День кадровика",
        {
            "type": "professional",
            "profession": "hr",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "team",
            "audience": "role-based",
            "prompt_hint": "Сильная команда, развитие людей, корпоративная культура",
        },
    ),
    "marketing": HolidayRule(
        10,
        25,
        "День маркетолога",
        {
            "type": "professional",
            "profession": "marketing",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "growth",
            "audience": "role-based",
            "prompt_hint": "Идеи, рост бренда, сильные коммуникации, новые рынки",
        },
    ),
    "sales": HolidayRule(
        7,
        23,
        "День работника торговли",
        {
            "type": "professional",
            "profession": "sales",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "sales",
            "audience": "role-based",
            "prompt_hint": "Клиенты, продажи, уверенные переговоры, рост результата",
        },
    ),
    "logistics": HolidayRule(
        11,
        28,
        "День логиста",
        {
            "type": "professional",
            "profession": "logistics",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "operations",
            "audience": "role-based",
            "prompt_hint": "Надёжные процессы, слаженная работа, устойчивые цепочки поставок",
        },
    ),
    "construction": HolidayRule(
        8,
        11,
        "День строителя",
        {
            "type": "professional",
            "profession": "construction",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "growth",
            "audience": "role-based",
            "prompt_hint": "Созидание, развитие, масштаб, прочные результаты",
        },
    ),
    "medicine": HolidayRule(
        6,
        16,
        "День медицинского работника",
        {
            "type": "professional",
            "profession": "medicine",
            "tone_hint": "warm",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "care",
            "audience": "role-based",
            "prompt_hint": "Забота, внимание к людям, значимость работы, доверие",
        },
    ),
    "finance": HolidayRule(
        9,
        8,
        "День финансиста",
        {
            "type": "professional",
            "profession": "finance",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "finance",
            "audience": "role-based",
            "prompt_hint": "Финансовая устойчивость, точность, взвешенные решения",
        },
    ),
    "management": HolidayRule(
        9,
        27,
        "День руководителя",
        {
            "type": "professional",
            "profession": "management",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "leadership",
            "audience": "role-based",
            "prompt_hint": "Лидерство, развитие команды, сильные управленческие решения",
        },
    ),
    "security": HolidayRule(
        12,
        20,
        "День специалиста по безопасности",
        {
            "type": "professional",
            "profession": "security",
            "tone_hint": "official",
            "source": "builtin",
            "category": "professional",
            "focus_hint": "stability",
            "audience": "role-based",
            "prompt_hint": "Надёжность, устойчивость, защита процессов и доверия",
        },
    ),
}


def general_holidays_in_window(*, today: dt.date, end: dt.date) -> list[tuple[dt.date, str, dict]]:
    years = {today.year, end.year}
    out: list[tuple[dt.date, str, dict]] = []
    for year in sorted(years):
        for rule in _GENERAL_HOLIDAYS:
            date_value = dt.date(year, rule.month, rule.day)
            if today <= date_value <= end:
                out.append((date_value, rule.title, dict(rule.tags)))
    return out


def professional_holidays_for_client(
    *, profession: str, today: dt.date, end: dt.date
) -> list[tuple[dt.date, str, dict]]:
    prof = (profession or "").strip().lower()
    rule = _PROFESSIONAL_HOLIDAYS.get(prof)
    if rule is None:
        return []

    years = {today.year, end.year}
    out: list[tuple[dt.date, str, dict]] = []
    for year in sorted(years):
        if prof == "it":
            date_value = _programmer_day(year)
        else:
            date_value = dt.date(year, rule.month, rule.day)
        if today <= date_value <= end:
            out.append((date_value, rule.title, dict(rule.tags)))
    return out
