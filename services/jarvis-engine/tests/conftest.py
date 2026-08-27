"""Shared fixtures for tests that exercise the FastAPI app directly."""
import pytest
from starlette.testclient import TestClient

from jarvis_engine.core.config import settings

# Set BEFORE importing main/app so the value is in place by the time the
# lifespan runs. Entering TestClient(app) executes the app's REAL startup,
# which otherwise means faster-whisper downloading `small.en` from
# HuggingFace on a cold cache and openWakeWord opening the OS microphone -
# in a test run. That made the suite network-dependent, slow, and a
# contender for the audio device against every other test.
#
# The handler wiring in voice_manager.initialize() still happens; only the
# two model-loading threads are skipped. Tests that exercise voice logic
# drive voice_manager directly with their own mocks and are unaffected.
settings.VOICE_DISABLED = True

from jarvis_engine.main import app  # noqa: E402
from jarvis_engine.core.database import set_setting  # noqa: E402
from jarvis_engine.providers.manager import provider_manager  # noqa: E402


@pytest.fixture(scope="session")
def api_client():
    """Single shared TestClient for the whole test session.

    Entering TestClient(app) runs the app's real lifespan - including
    opening an actual microphone stream for the wake-word detector and
    kicking off the TTS loader thread. Tests that each did their own
    `with TestClient(app) as client:` were opening/closing that mic stream
    once per test; back-to-back cycles of that raced the OS audio device
    and produced an intermittent hang/crash when run as a full-file batch
    (reproduced: passed in isolation, hung/failed as part of the file).
    Sharing one client for the whole session runs that lifespan exactly
    once, eliminating the race.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
async def _reset_provider_state():
    """Provider-cascade tests mutate global, process-wide state:
    provider_manager.providers (the singleton's active provider list, the
    same object every route module imports) and the
    provider_override/fallback_mode/awaiting_provider_choice/
    preferred_provider/preferred_model settings in the real settings
    table. Reset both BEFORE and AFTER every test - not
    just after - so state left behind by a test that errors before
    reaching its own cleanup, or by test ordering, can never leak into the
    next test.
    """
    original_providers = list(provider_manager.providers)

    async def _reset_settings():
        await set_setting("provider_override", "")
        await set_setting("fallback_mode", "auto")
        await set_setting("awaiting_provider_choice", "false")
        await set_setting("preferred_provider", "")
        await set_setting("preferred_model", "")

    await _reset_settings()
    provider_manager.providers = list(original_providers)

    yield

    provider_manager.providers = list(original_providers)
    await _reset_settings()
