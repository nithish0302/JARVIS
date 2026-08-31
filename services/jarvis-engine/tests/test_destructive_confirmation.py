"""Regression tests for the backend destructive-action guard.

Two bugs motivated these:

C1 - /voice/input never called enforce_destructive_confirmation(). /chat
     and /chat/stream both did. A spoken request that produced a
     [UI_ACTION:send_email:...] tag went to the frontend unwrapped, and
     the frontend executed it on arrival: mail sent off a raw transcript
     with no confirmation step.

H1 - The guard was four copy-pasted regex blocks, one per action, so it
     was possible to wrap an action here while forgetting the matching
     execution handler on the frontend (which is exactly what happened to
     create_github_issue).

The endpoint tests are parametrized over DESTRUCTIVE_UI_ACTIONS rather
than listing actions literally, so adding an entry to that tuple
automatically extends coverage instead of quietly leaving the new action
untested.

Uses the shared session-scoped `api_client` fixture (see conftest.py)
rather than opening a fresh TestClient(app) per test - each entry/exit
runs the app's real lifespan, and doing that once per parametrized case
reliably crashed the run.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jarvis_engine.api.routes import (
    DESTRUCTIVE_UI_ACTIONS,
    enforce_destructive_confirmation,
)
from jarvis_engine.providers.manager import provider_manager


def _provider(response_text: str):
    p = MagicMock()
    p.name = "ollama"
    p.model = "phi4-mini"
    p.is_available = AsyncMock(return_value=True)
    p.chat = AsyncMock(return_value=response_text)
    return p


def _quiet_request(providers):
    """Pin the request to the plain LLM path: no search, no filesystem
    branch, no automation - so the assertions are about the guard only."""
    return (
        patch.object(provider_manager, "providers", providers),
        patch("jarvis_engine.api.routes.needs_web_search", return_value=False),
        patch(
            "jarvis_engine.api.routes.is_file_system_command", return_value=(False, {})
        ),
        patch("jarvis_engine.api.routes.needs_automation", return_value=False),
    )


# --------------------------------------------------------------------------
# The guard itself
# --------------------------------------------------------------------------


@pytest.mark.parametrize("action", DESTRUCTIVE_UI_ACTIONS)
def test_every_destructive_action_is_rewritten_to_confirm_action(action):
    """Each action in the single source of truth actually gets wrapped."""
    raw = f"Right away, sir. [UI_ACTION:{action}:some:payload:here]"

    result = enforce_destructive_confirmation(raw)

    assert f"[UI_ACTION:confirm_action:{action}:some:payload:here]" in result
    assert f"[UI_ACTION:{action}:" not in result


def test_non_destructive_actions_pass_through_untouched():
    raw = (
        "It's 14 degrees and clear, sir. "
        "[UI_ACTION:check_weather:London][UI_ACTION:open_app:notepad]"
    )
    assert enforce_destructive_confirmation(raw) == raw


def test_already_confirmed_actions_are_not_double_wrapped():
    """confirm_action:send_email must not become
    confirm_action:confirm_action:send_email on a second pass."""
    once = enforce_destructive_confirmation(
        "[UI_ACTION:send_email:a@b.com:Subject:Body]"
    )
    twice = enforce_destructive_confirmation(once)
    assert once == twice
    assert "confirm_action:confirm_action" not in twice


def test_multiple_destructive_actions_in_one_response_all_rewritten():
    raw = (
        "[UI_ACTION:send_email:a@b.com:Hi:There]"
        "[UI_ACTION:create_github_issue:me/repo:Bug:It broke]"
    )
    result = enforce_destructive_confirmation(raw)
    assert "[UI_ACTION:confirm_action:send_email:a@b.com:Hi:There]" in result
    assert (
        "[UI_ACTION:confirm_action:create_github_issue:me/repo:Bug:It broke]" in result
    )


# --------------------------------------------------------------------------
# C1: the voice path must apply the guard
# --------------------------------------------------------------------------


@pytest.mark.parametrize("action", DESTRUCTIVE_UI_ACTIONS)
def test_voice_input_applies_destructive_confirmation(api_client, action):
    """THE C1 REGRESSION TEST.

    /voice/input must wrap destructive actions exactly as /chat does. If
    this fails, a spoken command can execute a destructive action with no
    confirmation step.
    """
    providers, no_search, no_fs, no_auto = _quiet_request(
        [_provider(f"Done, sir. [UI_ACTION:{action}:target:payload]")]
    )

    with providers, no_search, no_fs, no_auto:
        res = api_client.post("/voice/input", json={"text": f"please {action}"})

    assert res.status_code == 200
    body = res.json()["response"]

    assert f"[UI_ACTION:confirm_action:{action}:target:payload]" in body, (
        f"/voice/input returned an UNCONFIRMED {action} action. "
        f"enforce_destructive_confirmation() is not being applied to the "
        f"voice response path. Response was: {body!r}"
    )
    assert f"[UI_ACTION:{action}:" not in body


def test_voice_input_leaves_safe_actions_alone(api_client):
    """The guard must not turn ordinary voice actions into confirmation
    prompts - that would make every 'what's the weather' need a click."""
    providers, no_search, no_fs, no_auto = _quiet_request(
        [_provider("It's clear, sir. [UI_ACTION:check_weather:London]")]
    )

    with providers, no_search, no_fs, no_auto:
        res = api_client.post("/voice/input", json={"text": "what's the weather"})

    body = res.json()["response"]
    assert "[UI_ACTION:check_weather:London]" in body
    assert "confirm_action" not in body


def test_chat_still_applies_destructive_confirmation(api_client):
    """Regression guard on the path that already worked, so the refactor
    from four regex blocks to a loop can't have broken it."""
    providers, no_search, no_fs, no_auto = _quiet_request(
        [_provider("Sending now. [UI_ACTION:send_email:a@b.com:Hi:There]")]
    )

    with providers, no_search, no_fs, no_auto:
        res = api_client.post(
            "/chat",
            json={
                "message": "email a@b.com saying hi",
                "conversation_id": None,
                "provider": "ollama",
                "model": "phi4-mini",
            },
        )

    assert res.status_code == 200
    body = res.json()["response"]
    assert "[UI_ACTION:confirm_action:send_email:a@b.com:Hi:There]" in body
    assert "[UI_ACTION:send_email:" not in body


def test_voice_and_chat_produce_identical_guard_output(api_client):
    """The parity check the audit asked for: the same model output must
    come back identically guarded whichever endpoint produced it. This is
    the assertion that fails first if the two paths drift again."""
    raw = "Filing it. [UI_ACTION:create_github_issue:me/repo:Bug:Broken]"
    expected = "[UI_ACTION:confirm_action:create_github_issue:me/repo:Bug:Broken]"

    providers, no_search, no_fs, no_auto = _quiet_request([_provider(raw)])
    with providers, no_search, no_fs, no_auto:
        voice = api_client.post(
            "/voice/input", json={"text": "file a github issue"}
        ).json()["response"]

    providers, no_search, no_fs, no_auto = _quiet_request([_provider(raw)])
    with providers, no_search, no_fs, no_auto:
        chat = api_client.post(
            "/chat",
            json={
                "message": "file a github issue",
                "conversation_id": None,
                "provider": "ollama",
                "model": "phi4-mini",
            },
        ).json()["response"]

    assert expected in voice
    assert expected in chat
