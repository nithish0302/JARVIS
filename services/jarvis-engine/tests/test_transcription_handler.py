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

    return posts, spoken


def _settle(posts, expected, timeout=3.0):
    """Handler dispatches to a daemon thread; wait for it to finish."""
    deadline = time.time() + timeout
    while len(posts) < expected and time.time() < deadline:
        time.sleep(0.02)


def test_signature_matches_call_site():
    """voice_manager calls on_transcription(text, direct_result)."""
    params = list(inspect.signature(th.handle_transcription).parameters)
    assert params == ["text", "direct_result"]


def test_direct_command_branch_completes(captured):
    posts, spoken = captured

    th.handle_transcription("open notepad", "Opening Notepad, sir.")
    _settle(posts, 3)

    urls = [u for u, _ in posts]
    payloads = [j for _, j in posts]

    # Broadcast carries the already-executed result as direct_response
    assert any(j and j.get("direct_response") == "Opening Notepad, sir." for j in payloads)
    # It was actually spoken
    assert spoken == ["Opening Notepad, sir."]
    # Status went speaking -> idle
    statuses = [j.get("status") for j in payloads if j and "status" in j]
    assert "speaking" in statuses
    assert statuses[-1] == "idle"


def test_llm_branch_completes(captured):
    posts, spoken = captured

    th.handle_transcription("what is the weather like", None)
    _settle(posts, 3)

    payloads = [j for _, j in posts]

    # Text posted without a direct_response, so the LLM pipeline runs
    assert any(j and j.get("text") == "what is the weather like"
               and "direct_response" not in j for j in payloads)
    # The LLM's response was spoken
    assert spoken == ["The weather is clear, sir."]

    statuses = [j.get("status") for j in payloads if j and "status" in j]
    assert statuses[-1] == "idle"


def test_returns_to_idle_when_tts_fails(captured, monkeypatch):
    """A TTS failure must not strand the orb in 'speaking'."""
    posts, spoken = captured

    import jarvis_engine.voice.tts_engine as te

    def boom(text, on_speech_start=None):
        raise RuntimeError("tts exploded")

    monkeypatch.setattr(te.tts_engine, "speak_sync", boom, raising=False)

    th.handle_transcription("open notepad", "Opening Notepad, sir.")
    _settle(posts, 3)

    statuses = [j.get("status") for _, j in posts if j and "status" in j]
    assert statuses[-1] == "idle", "status stuck after TTS error"


def test_voice_start_route_uses_the_shared_handler():
    """The /voice/start route must not re-install a 1-arg stub."""
    import jarvis_engine.api.routes as routes

    src = inspect.getsource(routes.start_voice)
    assert "handle_transcription" in src
    assert "def on_transcription" not in src
