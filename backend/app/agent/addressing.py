from __future__ import annotations

import re

from app.db.models import Client


def infer_gender_hint(*, first_name: str | None, middle_name: str | None) -> str | None:
    middle = (middle_name or "").strip().lower()
    first = (first_name or "").strip().lower()

    if middle.endswith("ич"):
        return "male"
    if middle.endswith("на"):
        return "female"

    female_name_exceptions = {
        "любовь",
        "нино",
    }
    male_name_exceptions = {
        "никита",
        "илья",
        "кузьма",
        "фома",
        "лука",
    }

    if first in female_name_exceptions:
        return "female"
    if first in male_name_exceptions:
        return "male"
    if first.endswith(("а", "я")):
        return "female"
    return None


def build_formal_name(*, first_name: str | None, middle_name: str | None) -> str:
    first = (first_name or "").strip()
    middle = (middle_name or "").strip()
    return " ".join(part for part in (first, middle) if part).strip() or first


def build_respectful_greeting(*, first_name: str | None, middle_name: str | None) -> str:
    formal_name = build_formal_name(first_name=first_name, middle_name=middle_name)
    gender = infer_gender_hint(first_name=first_name, middle_name=middle_name)
    prefix = "Уважаемая" if gender == "female" else "Уважаемый"
    if formal_name:
        return f"{prefix} {formal_name}"
    return prefix


def normalize_generated_salutation(body: str, *, client: Client) -> str:
    text = body or ""
    first_name = (client.first_name or "").strip()
    middle_name = (getattr(client, "middle_name", None) or "").strip()
    last_name = (client.last_name or "").strip()
    if not text or not first_name:
        return text

    respectful = build_respectful_greeting(first_name=first_name, middle_name=middle_name)
    formal_name = build_formal_name(first_name=first_name, middle_name=middle_name)

    if middle_name and last_name:
        respectful_with_last = f"(Уважаемый|Уважаемая)\\s+{re.escape(first_name)}\\s+{re.escape(middle_name)}\\s+{re.escape(last_name)}"
        text = re.sub(respectful_with_last, respectful, text, count=1)

        plain_with_last = (
            f"{re.escape(first_name)}\\s+{re.escape(middle_name)}\\s+{re.escape(last_name)}"
        )
        text = re.sub(plain_with_last, formal_name, text, count=1)

    if middle_name:
        wrong_prefix = f"Уважаемый\\s+{re.escape(first_name)}\\s+{re.escape(middle_name)}"
        if respectful.startswith("Уважаемая"):
            text = re.sub(wrong_prefix, respectful, text, count=1)
    return text
