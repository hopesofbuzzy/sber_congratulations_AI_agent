from __future__ import annotations

import httpx

from app.db.session import get_session
from app.main import create_app


async def test_dashboard_page_renders_new_presentation_layout(db_session):
    app = create_app()

    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "Sber congratulations pipeline" in resp.text
    assert "Presentation-ready workspace" in resp.text
    assert "How to present the demo" in resp.text


async def test_clients_page_renders_enrichment_ui(db_session):
    app = create_app()

    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/clients")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "Data quality overview" in resp.text
    assert "Enrich company profiles" in resp.text
    assert "Добавить клиента вручную" in resp.text
