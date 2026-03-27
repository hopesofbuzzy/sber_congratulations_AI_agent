from __future__ import annotations

from app.agent.text_generator import generate_text
from app.services.template_selector import choose_template


def test_text_generator_uses_enriched_company_context():
    choice = choose_template(segment="standard", event_type="holiday", title="День финансиста")
    subject, body = generate_text(
        choice,
        context={
            "first_name": "Павел",
            "middle_name": "Игоревич",
            "last_name": "Сафронов",
            "company_name": "ЗАО ТехСтрой",
            "official_company_name": 'ЗАО "ТехСтрой"',
            "position": "Финансовый директор",
            "okved_name": "Строительство жилых и нежилых зданий",
        },
        title="День финансиста",
    )
    assert "День финансиста" in subject
    assert 'ЗАО "ТехСтрой"' in body
    assert "Строительство жилых и нежилых зданий" in body
