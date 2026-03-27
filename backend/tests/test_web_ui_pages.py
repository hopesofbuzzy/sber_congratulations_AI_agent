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
    assert "Конвейер поздравлений Сбера" in resp.text
    assert "Рабочее пространство для презентации" in resp.text
    assert "Как показать демо" in resp.text


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
    assert "Качество данных" in resp.text
    assert "Импортировать базу компаний" in resp.text
    assert "Обогатить профили компаний" in resp.text
    assert "Добавить клиента вручную" in resp.text


async def test_events_page_renders_manual_event_controls(db_session):
    app = create_app()

    async def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/events")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "Создать ручное событие" in resp.text
    assert "Быстрая demo-кампания" in resp.text
    assert "Подготовить события для реальной базы" in resp.text
