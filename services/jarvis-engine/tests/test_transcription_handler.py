"""Regression tests for the voice transcription handler (BUG A).

POST /voice/start used to install a 1-argument M2-era stub that clobbered
the real handler, so every real transcription died with:

    on_transcription() takes 1 positional argument but 2 were given

These tests assert the signature matches the call site AND that both
dispatch branches actually complete end-to-end (broadcast + speak +
return to idle), not merely that no exception is raised.
"""

import inspect
import sys
import time
from unittest.mock import MagicMock

import pytest

import jarvis_engine.voice.transcription_handler as th


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def captured(monkeypatch):
    """Capture POSTs and TTS output instead of hitting the network/speakers."""
    posts = []
    spoken = []

    class FakeRequests:
        @staticmethod
        def post(url, json=None, timeout=None):
            posts.append((url, json))
            return FakeResponse({"response": "The weather is clear, sir."})

    class FakeTTS:
        is_speaking = False
        last_speech_end_time = 0.0

        def speak_sync(self, text, on_speech_start=None):
            if on_speech_start is not None:
                on_speech_start()
            spoken.append(text)

    # The handler imports `requests` and the tts_engine lazily inside its
    # worker threads, so patch at module level.
    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    import jarvis_engine.voice.tts_engine as te

    monkeypatch.setattr(te, "tts_engine", FakeTTS(), raising=False)

    # _speak_response hands off to continuous conversation mode
    # (voice_manager.continue_conversation()) once TTS finishes - that's
    # covered by its own tests in test_continuous_mode.py. Here it's mocked
    # to a no-op so these handler-level tests don't spawn a real recording
    # thread / touch the microphone.
    import jarvis_engine.voice.voice_manager as vm

    monkeypatch.setattr(
        vm.voice_manager, "continue_conversation", MagicMock(), raising=False
    )

    return posts, spoken


def _settle(posts, expected, timeout=3.0):
    """Handler dispatches to a daemon thread; wait for it to finish."""
    deadline = time.time() + timeout
    while len(posts) < expected and time.time() < deadline:
        time.sleep(0.02)
    # continue_conversation() is the last statement in _speak_response's
    # finally block, i.e. it can run a hair after the post count above is
    # already satisfied - give it a moment too so assert_called_once()
    # right after _settle() isn't a race.
    time.sleep(0.02)


def test_signature_matches_call_site():
    """voice_manager calls on_transcription(text, direct_result)."""
    params = list(inspect.signature(th.handle_transcription).parameters)
    assert params == ["text", "direct_result", "conversation_id"]


def test_direct_command_branch_completes(captured):
    posts, spoken = captured

    th.handle_transcription("open notepad", "Opening Notepad, sir.")
    _settle(posts, 2)

    urls = [u for u, _ in posts]
    payloads = [j for _, j in posts]

    # Broadcast carries the already-executed result as direct_response
    assert any(
        j and j.get("direct_response") == "Opening Notepad, sir." for j in payloads
    )
    # It was actually spoken
    assert spoken == ["Opening Notepad, sir."]
    # Status went to speaking - the finally block hands off to continuous
    # mode (mocked here) instead of broadcasting "idle" itself, so it never
    # gets a chance to strand the orb mid-response either.
    statuses = [j.get("status") for j in payloads if j and "status" in j]
    assert "speaking" in statuses

    import jarvis_engine.voice.voice_manager as vm

    vm.voice_manager.continue_conversation.assert_called_once()


def test_llm_branch_completes(captured):
    posts, spoken = captured

    th.handle_transcription("what is the weather like", None)
    _settle(posts, 2)

    payloads = [j for _, j in posts]

    # Text posted without a direct_response, so the LLM pipeline runs
    assert any(
        j and j.get("text") == "what is the weather like" and "direct_response" not in j
        for j in payloads
    )
    # The LLM's response was spoken
    assert spoken == ["The weather is clear, sir."]

    import jarvis_engine.voice.voice_manager as vm

    vm.voice_manager.continue_conversation.assert_called_once()


def test_continue_conversation_called_even_when_tts_fails(captured, monkeypatch):
    """A TTS failure must not strand the orb - continue_conversation()
    (which decides the next status, "continuous" or "idle") must still be
    reached via the finally block."""
    posts, spoken = captured

    import jarvis_engine.voice.tts_engine as te

    def boom(text, on_speech_start=None):
        raise RuntimeError("tts exploded")

    monkeypatch.setattr(te.tts_engine, "speak_sync", boom, raising=False)

    th.handle_transcription("open notepad", "Opening Notepad, sir.")
    _settle(posts, 1)

    import jarvis_engine.voice.voice_manager as vm

    vm.voice_manager.continue_conversation.assert_called_once()


def test_voice_start_route_uses_the_shared_handler():
    """The /voice/start route must not re-install a 1-arg stub."""
    from jarvis_engine.api import routes

    src = inspect.getsource(routes.start_voice)
    assert "handle_transcription" in src
    assert "def on_transcription" not in src
