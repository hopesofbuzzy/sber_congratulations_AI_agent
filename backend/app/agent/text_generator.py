from __future__ import annotations

from app.services.template_selector import TemplateChoice


def _extra_line(context: dict) -> str:
    company = context.get("official_company_name") or context.get("company_name")
    position = context.get("position")
    okved_name = context.get("okved_name")
    manual_kind = context.get("manual_kind")
    focus_hint = context.get("focus_hint")
    holiday_focus_hint = context.get("holiday_focus_hint")
    holiday_category = context.get("holiday_category")
    event_greeting_guidance = context.get("event_greeting_guidance")

    bits: list[str] = []
    if company:
        bits.append(f"Успехов вашей команде в {company}.")
    if position:
        bits.append(f"Пусть работа в роли «{position}» приносит вдохновение и сильные результаты.")
    if okved_name:
        bits.append(
            f"Пусть проекты в направлении «{okved_name}» приносят вашей команде устойчивый рост и новые возможности."
        )
    if manual_kind == "business_touchpoint":
        bits.append(
            "Пусть текущее деловое взаимодействие откроет для вашей команды ещё больше возможностей для развития и уверенных решений."
        )
    manual_focus_lines = {
        "finance": "Желаем вашей команде финансовой устойчивости, взвешенных решений и спокойного движения к новым результатам.",
        "operations": "Пусть рабочие процессы остаются надёжными, а каждый новый этап приносит вашей команде устойчивый рост.",
        "sales": "Желаем расширения клиентской базы, сильных переговоров и уверенного движения к новым коммерческим результатам.",
        "technology": "Пусть технологические инициативы вашей команды помогают быстро двигаться вперёд и открывают новые возможности.",
        "leadership": "Пусть управленческие решения помогают команде уверенно развивать бизнес и сохранять сильный темп роста.",
        "team": "Желаем сильной команды, продуктивного взаимодействия и устойчивого развития на каждом следующем этапе.",
        "growth": "Пусть впереди будет больше сильных инициатив, устойчивого роста и уверенных деловых результатов.",
        "care": "Пусть ваша работа и дальше приносит значимые результаты, доверие и устойчивое развитие команды.",
        "stability": "Желаем надёжности, устойчивости и уверенного движения к новым деловым результатам.",
    }
    if focus_hint in manual_focus_lines:
        bits.append(manual_focus_lines[focus_hint])
    holiday_focus_lines = {
        "renewal": "Пусть этот этап принесёт вашей команде обновление, уверенный старт новых инициатив и сильный импульс к развитию.",
        "respect": "Желаем уверенности, внутренней силы и уважения, которое чувствуется в каждом профессиональном результате.",
        "care": "Пусть рядом будет больше тёплых людей, вдохновения и поводов гордиться своими ежедневными результатами.",
        "team": "Желаем слаженной команды, сильной поддержки коллег и уверенного движения к общим целям.",
        "gratitude": "Пусть в работе и жизни будет больше достойных поводов для гордости, уважения и благодарности.",
        "growth": "Желаем масштабных возможностей, здоровой предпринимательской энергии и уверенного роста во всех сильных направлениях.",
        "stability": "Пусть решения остаются взвешенными, процессы надёжными, а результаты устойчивыми на длинной дистанции.",
        "finance": "Желаем финансовой устойчивости, точности в решениях и уверенного движения к новым сильным результатам.",
        "technology": "Пусть новые идеи, технологии и смелые решения помогают вашей команде двигаться вперёд быстрее и увереннее.",
        "sales": "Желаем сильных коммуникаций, доверия клиентов и новых убедительных коммерческих результатов.",
        "operations": "Пусть процессы остаются слаженными, устойчивыми и помогают вашей команде сохранять высокий темп работы.",
        "leadership": "Желаем сильных управленческих решений, устойчивой команды и уверенного развития бизнеса на каждом этапе.",
    }
    if holiday_focus_hint in holiday_focus_lines:
        bits.append(holiday_focus_lines[holiday_focus_hint])
    if holiday_category == "business":
        bits.append(
            "Пусть деловые инициативы приносят вашей команде устойчивый рост, сильные партнёрства и новые возможности для развития."
        )
    if event_greeting_guidance:
        bits.append(str(event_greeting_guidance))
    # Do not expose last interaction topic in greetings (privacy / tone). Keep generic gratitude.
    bits.append("Спасибо, что остаётесь с нами.")

    if not bits:
        return ""
    return "\n\n" + " ".join(bits)


def generate_text(choice: TemplateChoice, *, context: dict, title: str) -> tuple[str, str]:
    """Generate (subject, body).

    MVP: deterministic template rendering + small personalization line.
    (External LLM provider can be plugged later behind the same interface.)
    """

    subject = choice.subject_template.format(**context, title=title).strip()
    body = choice.body_template.format(**context, title=title).rstrip()
    body = body + _extra_line(context)
    return subject, body
