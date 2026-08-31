"""Regression test for a crash where an LLM response containing a
character the console can't encode (confirmed: Groq returning a narrow
no-break space, U+202F) turned a successful /voice/input request into an
unhandled 500 via UnicodeEncodeError in print(). This must not depend on
PYTHONIOENCODING being set externally - the fix must hold under a
Windows-cp1252-like stdout with no such env var."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from jarvis_engine.core.utils import safe_print
from jarvis_engine.main import app

NARROW_NO_BREAK_SPACE = " "


class Cp1252LikeStdout(io.TextIOWrapper):
    """Stands in for Windows' default console stream: any character
    outside cp1252 raises UnicodeEncodeError on write, exactly like the
    real console did before the fix - with no PYTHONIOENCODING involved."""

    def __init__(self):
        super().__init__(io.BytesIO(), encoding="cp1252", errors="strict")


def _fake_provider(response_text: str):
    provider = MagicMock()
    provider.name = "groq"
    provider.model = "llama-3.3-70b"
    provider.is_available = AsyncMock(return_value=True)
    provider.chat = AsyncMock(return_value=response_text)
    return provider


def test_safe_print_does_not_raise_on_unencodable_console_char():
    stream = Cp1252LikeStdout()

    # Sanity check: a bare print() to this stream really does crash on the
    # confirmed offending character, proving the test stream reproduces
    # the original bug before we assert the fix works around it.
    with pytest.raises(UnicodeEncodeError):
        print(f"probe{NARROW_NO_BREAK_SPACE}probe", file=stream)

    # safe_print() must not raise on the same input/stream.
    safe_print(f"probe{NARROW_NO_BREAK_SPACE}probe", file=stream)


def test_voice_input_with_unicode_response_succeeds_without_pythonioencoding():
    response_text = f"Certainly, sir.{NARROW_NO_BREAK_SPACE}Right away."
    provider = _fake_provider(response_text)

    with (
        patch("jarvis_engine.api.routes.provider_manager") as mock_pm,
        patch("sys.stdout", Cp1252LikeStdout()),
    ):
        mock_pm.providers = [provider]

        with TestClient(app) as client:
            res = client.post("/voice/input", json={"text": "what's the plan"})

    assert res.status_code == 200
    body = res.json()
    assert NARROW_NO_BREAK_SPACE in body["response"]
