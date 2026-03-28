from __future__ import annotations

from app.agent.gigachat_client import GigaChatClient
from app.agent.gigachat_providers import GigaChatImageProvider, build_illustration_prompt
from app.core.config import settings


def test_gigachat_prompt_avoids_card_word_and_forbids_text():
    system, user = build_illustration_prompt(
        event_type="birthday",
        event_title="День рождения",
        recipient_line="Иван Тестов",
        company="ООО Пример",
    )
    low = (system + "\n" + user).lower()
    assert "открытк" not in low
    assert "без текста" in low or "никакого текста" in low


def test_gigachat_prompt_uses_semantic_business_context():
    system, user = build_illustration_prompt(
        event_type="holiday",
        event_title="День российского предпринимательства",
        recipient_line="Иван Тестов",
        company="ООО Вектор",
        event_details={
            "holiday_tags": {
                "category": "business",
                "focus_hint": "growth",
                "prompt_hint": "Предпринимательская энергия, развитие бизнеса, новые возможности",
                "audience": "business",
            }
        },
        segment="vip",
        profession="management",
    )
    low = (system + "\n" + user).lower()
    assert "открытк" not in low
    assert "развитие бизнеса" in low
    assert "город" in low or "развит" in low


async def test_gigachat_image_provider_uses_image_generation_timeout(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_chat_completions(self, **kwargs):
        captured["timeout_sec"] = kwargs.get("timeout_sec")
        return {"choices": [{"message": {"content": '<img src="file-123" />'}}]}

    async def fake_download_file_content(self, *, file_id: str, x_client_id: str | None = None):
        captured["file_id"] = file_id
        captured["x_client_id"] = x_client_id
        return b"jpg-bytes"

    monkeypatch.setattr(settings, "gigachat_credentials", "test-creds", raising=False)
    monkeypatch.setattr(settings, "gigachat_image_generation_timeout_sec", 123.0, raising=False)
    monkeypatch.setattr(GigaChatClient, "chat_completions", fake_chat_completions)
    monkeypatch.setattr(GigaChatClient, "download_file_content", fake_download_file_content)

    provider = GigaChatImageProvider()
    file_id, jpg = await provider.generate_jpg(
        system_style="style",
        prompt="prompt",
        x_client_id="42",
    )

    assert captured["timeout_sec"] == 123.0
    assert captured["file_id"] == "file-123"
    assert captured["x_client_id"] == "42"
    assert file_id == "file-123"
    assert jpg == b"jpg-bytes"
