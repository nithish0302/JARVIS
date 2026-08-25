"""Tests for the dynamic model badge / fallback notification / provider
override feature: verifies provider_used + model_used are accurate
(including the voice endpoint, which used to hardcode model_used="voice"),
that a fallback is reported via fallback_occurred/failed_provider, that
provider_override restricts the cascade to exactly one provider with no
silent substitution, and that fallback_mode="ask" pauses on a failure and
routes the user's next message to the provider they name.

Uses the shared session-scoped `api_client` fixture (see conftest.py)
rather than opening a fresh TestClient(app) per test - each entry/exit
triggers the app's real lifespan (mic stream open/close for the wake-word
detector), and doing that once per test in this file was the source of an
intermittent hang/crash when run as a full-file batch. The
`_reset_provider_state` autouse fixture (also conftest.py) resets
provider_manager.providers and the provider_override/fallback_mode/
awaiting_provider_choice settings before AND after every test."""
from unittest.mock import AsyncMock, MagicMock, patch

from jarvis_engine.core.database import set_setting
from jarvis_engine.providers.manager import provider_manager


def _provider(name: str, model: str, *, available=True, chat_result=None, chat_error=None):
    p = MagicMock()
    p.name = name
    p.model = model
    p.is_available = AsyncMock(return_value=available)
    if chat_error is not None:
        p.chat = AsyncMock(side_effect=chat_error)
    else:
        p.chat = AsyncMock(return_value=chat_result or f"response from {name}")
    return p


def _patch_providers(providers):
    return patch.object(provider_manager, "providers", providers)


def test_chat_endpoint_reports_accurate_provider_and_no_fallback_by_default(api_client):
    """Regression check: default auto cascade, first provider succeeds ->
    fallback_occurred must be False and provider_used/model_used must match
    exactly what answered."""
    gemini = _provider("gemini", "gemini-3.6-flash")
    groq = _provider("groq", "openai/gpt-oss-20b")

    with _patch_providers([gemini, groq]), \
         patch("jarvis_engine.api.routes.needs_web_search", return_value=False), \
         patch("jarvis_engine.api.routes.is_file_system_command", return_value=(False, {})), \
         patch("jarvis_engine.api.routes.needs_automation", return_value=False):
        res = api_client.post("/chat", json={
            "message": "hello", "conversation_id": None,
            "provider": "gemini", "model": "gemini-3.6-flash"
        })

    assert res.status_code == 200
    body = res.json()
    assert body["provider_used"] == "gemini"
    assert body["model_used"] == "gemini-3.6-flash"
    assert body["fallback_occurred"] is False
    assert body["failed_provider"] is None
    gemini.chat.assert_awaited_once()
    groq.chat.assert_not_awaited()


def test_chat_endpoint_reports_fallback_when_first_provider_fails(api_client):
    gemini = _provider("gemini", "gemini-3.6-flash", chat_error=RuntimeError("503"))
    groq = _provider("groq", "openai/gpt-oss-20b", chat_result="I'm Groq, sir.")

    with _patch_providers([gemini, groq]), \
         patch("jarvis_engine.api.routes.needs_web_search", return_value=False), \
         patch("jarvis_engine.api.routes.is_file_system_command", return_value=(False, {})), \
         patch("jarvis_engine.api.routes.needs_automation", return_value=False):
        res = api_client.post("/chat", json={
            "message": "hello", "conversation_id": None,
            "provider": "gemini", "model": "gemini-3.6-flash"
        })

    assert res.status_code == 200
    body = res.json()
    assert body["provider_used"] == "groq"
    assert body["model_used"] == "openai/gpt-oss-20b"
    assert body["fallback_occurred"] is True
    assert body["failed_provider"] == "gemini"


def test_voice_input_reports_accurate_model_used_not_hardcoded(api_client):
    """Regression check for the model_used='voice' bug: voice must report
    the real model name, exactly like chat does."""
    gemini = _provider("gemini", "gemini-3.6-flash", chat_result="Hello, sir.")

    with _patch_providers([gemini]):
        res = api_client.post("/voice/input", json={"text": "hi there"})

    assert res.status_code == 200
    body = res.json()
    assert body["provider_used"] == "gemini"
    assert body["model_used"] == "gemini-3.6-flash"
    assert body["model_used"] != "voice"


def test_voice_input_speaks_natural_fallback_note(api_client):
    gemini = _provider("gemini", "gemini-3.6-flash", chat_error=RuntimeError("quota"))
    groq = _provider("groq", "openai/gpt-oss-20b", chat_result="I'm here, sir.")

    with _patch_providers([gemini, groq]):
        res = api_client.post("/voice/input", json={"text": "what's up"})

    assert res.status_code == 200
    body = res.json()
    assert body["fallback_occurred"] is True
    assert body["failed_provider"] == "gemini"
    assert body["provider_used"] == "groq"
    # Natural spoken note prepended to the actual answer, not a separate
    # interruption.
    assert "Gemini" in body["response"]
    assert "Groq" in body["response"]
    assert "I'm here, sir." in body["response"]


async def test_provider_override_only_tries_that_provider_even_if_it_fails(api_client):
    """provider_override must never silently substitute another provider -
    Gemini/OpenRouter/Ollama must NEVER be attempted when locked to groq,
    regardless of whether groq itself succeeds or fails."""
    await set_setting("provider_override", "groq")

    gemini = _provider("gemini", "gemini-3.6-flash")
    openrouter = _provider("openrouter", "google/gemma-4-27b-it:free")
    groq = _provider("groq", "openai/gpt-oss-20b", available=False)
    ollama = _provider("ollama", "phi4-mini")

    with _patch_providers([gemini, openrouter, groq, ollama]):
        res = api_client.post("/voice/input", json={"text": "hello"})

    assert res.status_code == 200
    body = res.json()
    # Fails cleanly - no substitution.
    assert body["provider_used"] == "override_unavailable"
    gemini.chat.assert_not_awaited()
    openrouter.chat.assert_not_awaited()
    ollama.chat.assert_not_awaited()
    groq.chat.assert_not_awaited()

    await set_setting("provider_override", "groq")
    groq2 = _provider("groq", "openai/gpt-oss-20b", chat_result="Groq only, sir.")
    with _patch_providers([gemini, openrouter, groq2, ollama]):
        res = api_client.post("/voice/input", json={"text": "hello again"})

    assert res.status_code == 200
    body = res.json()
    assert body["provider_used"] == "groq"
    assert body["model_used"] == "openai/gpt-oss-20b"
    gemini.chat.assert_not_awaited()
    openrouter.chat.assert_not_awaited()
    ollama.chat.assert_not_awaited()


async def test_fallback_mode_ask_pauses_instead_of_auto_switching_then_routes_next_message(api_client):
    await set_setting("fallback_mode", "ask")

    gemini = _provider("gemini", "gemini-3.6-flash", chat_error=RuntimeError("down"))
    groq = _provider("groq", "openai/gpt-oss-20b", chat_result="Groq answering, sir.")

    with _patch_providers([gemini, groq]):
        res = api_client.post("/voice/input", json={"text": "hello"})

    assert res.status_code == 200
    body = res.json()
    # Did not auto-fallback to groq.
    assert body["provider_used"] == "asking"
    groq.chat.assert_not_awaited()

    # Next message names a provider - must actually route there.
    with _patch_providers([gemini, groq]):
        res2 = api_client.post("/voice/input", json={"text": "use groq"})

    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["provider_used"] == "groq"
    groq.chat.assert_awaited_once()
