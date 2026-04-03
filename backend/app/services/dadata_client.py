from __future__ import annotations

from collections.abc import Sequence

import httpx

from app.core.config import settings


class DadataConfigurationError(RuntimeError):
    pass


class DadataRequestError(RuntimeError):
    pass


def _split_csv(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


async def find_party_by_inn(inn: str) -> dict | None:
    api_key = (settings.dadata_api_key or "").strip()
    if not api_key:
        raise DadataConfigurationError("Не задан DADATA_API_KEY.")

    payload: dict[str, str | Sequence[str]] = {"query": inn}
    branch_type = (settings.dadata_party_branch_type or "").strip()
    if branch_type:
        payload["branch_type"] = branch_type
    party_type = (settings.dadata_party_type or "").strip()
    if party_type:
        payload["type"] = party_type
    statuses = _split_csv(settings.dadata_party_status)
    if statuses:
        payload["status"] = statuses

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
