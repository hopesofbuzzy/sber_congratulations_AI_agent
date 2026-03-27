from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Client

RESOURCES_DIR = Path(__file__).resolve().parents[1] / "resources"
REGISTRY_PATH = RESOURCES_DIR / "company_registry_demo.json"


@dataclass(frozen=True)
class CompanyProfile:
    inn: str
    official_company_name: str
    ceo_name: str
    okved_code: str
    okved_name: str
    company_site: str | None
    source_url: str | None
    aliases: tuple[str, ...] = ()


def _normalize_name(value: str | None) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[\"'`]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


@lru_cache(maxsize=1)
def _demo_registry() -> list[CompanyProfile]:
    if not REGISTRY_PATH.exists():
        return []
    raw_items = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        CompanyProfile(
            inn=str(item["inn"]),
            official_company_name=str(item["official_company_name"]),
            ceo_name=str(item["ceo_name"]),
            okved_code=str(item["okved_code"]),
            okved_name=str(item["okved_name"]),
            company_site=item.get("company_site"),
            source_url=item.get("source_url"),
            aliases=tuple(item.get("aliases", [])),
        )
        for item in raw_items
    ]


def lookup_company_profile(*, inn: str | None, company_name: str | None) -> CompanyProfile | None:
    norm_inn = re.sub(r"\D", "", inn or "")
    norm_company = _normalize_name(company_name)
    for item in _demo_registry():
        if norm_inn and item.inn == norm_inn:
            return item
        alias_names = {_normalize_name(item.official_company_name), *(_normalize_name(a) for a in item.aliases)}
        if norm_company and norm_company in alias_names:
            return item
    return None


async def enrich_client_company(
    session: AsyncSession,
    *,
    client: Client,
) -> dict:
    if not client.inn and not client.company_name:
        client.enrichment_status = "error"
        client.enrichment_error = "Для enrichment нужен хотя бы ИНН или название компании."
        await session.commit()
        return {"status": "error", "client_id": client.id, "reason": client.enrichment_error}

    client.enrichment_status = "pending"
    client.enrichment_error = None
    await session.commit()

    profile = lookup_company_profile(inn=client.inn, company_name=client.company_name)
    if profile is None:
        client.enrichment_status = "error"
        client.enrichment_error = (
            "Организация не найдена в demo registry. Укажите ИНН из демо-набора или заполните профиль вручную."
        )
        await session.commit()
        return {"status": "error", "client_id": client.id, "reason": client.enrichment_error}

    client.inn = profile.inn
    client.official_company_name = profile.official_company_name
    client.ceo_name = profile.ceo_name
    client.okved_code = profile.okved_code
    client.okved_name = profile.okved_name
    client.company_site = profile.company_site
    client.source_url = profile.source_url
    client.enrichment_status = "enriched"
    client.enrichment_error = None
    client.enriched_at = dt.datetime.now(dt.timezone.utc)
    await session.commit()
    return {"status": "enriched", "client_id": client.id, "inn": client.inn}


async def enrich_client_company_by_id(session: AsyncSession, *, client_id: int) -> dict:
    client = (await session.execute(select(Client).where(Client.id == client_id))).scalar_one()
    return await enrich_client_company(session, client=client)


async def enrich_missing_clients(session: AsyncSession) -> dict:
    clients = (
        await session.execute(
            select(Client).order_by(Client.id.asc())
        )
    ).scalars().all()
    processed = 0
    enriched = 0
    errors = 0
    for client in clients:
        if not client.inn and not client.company_name:
            continue
        if client.enrichment_status == "enriched":
            continue
        processed += 1
        result = await enrich_client_company(session, client=client)
        if result["status"] == "enriched":
            enriched += 1
        else:
            errors += 1
    return {
        "processed": processed,
        "enriched": enriched,
        "errors": errors,
    }
