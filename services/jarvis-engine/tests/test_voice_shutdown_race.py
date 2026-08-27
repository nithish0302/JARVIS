"""Regression tests for the shutdown/loader race that segfaulted the suite.

voice_manager.initialize() spawns two background loader threads and
returns immediately. shutdown() used to tear down straight away, so a
shutdown arriving while a loader was still constructing would:

  1. read self.wake_word_detector, which the loader had not assigned yet,
  2. see None and skip stop(),
  3. let the loader finish and open a mic InputStream nothing owns.

The native sounddevice callback was then live against objects being
freed, which is an access violation - the full pytest run died with
"Windows fatal exception: access violation" (exit 139) while the same
tests passed file-by-file.

shutdown() now joins the loader threads first (_await_loaders).
"""
import threading
import time

import pytest

from jarvis_engine.core.config import settings
from jarvis_engine.voice.voice_manager import VoiceManager


def test_shutdown_waits_for_a_slow_loader_before_tearing_down():
    """THE REGRESSION TEST.

    A loader that assigns its detector late must have finished before
    shutdown inspects that attribute - otherwise shutdown skips stop()
    and the detector leaks a live mic stream.
    """
    vm = VoiceManager()
    detector = _FakeDetector()
    started = threading.Event()

    def slow_loader():
        started.set()
        time.sleep(0.4)          # still constructing...
        vm.wake_word_detector = detector   # ...assigned only now
        vm.wake_word_ready.set()

    t = threading.Thread(target=slow_loader, name="wakeword-loader")
    vm._loader_threads = [t]
    t.start()
    started.wait(timeout=2)

    vm.shutdown()

    assert not t.is_alive(), "shutdown returned while a loader was still running"
    assert detector.stopped, (
        "shutdown did not stop the detector - it read wake_word_detector "
        "before the loader assigned it, which is the leak that crashed "
        "the interpreter."
    )
    assert vm.wake_word_detector is None


def test_shutdown_is_safe_immediately_after_initialize(monkeypatch):
    """Start/stop in quick succession is exactly the sequence the test
    suite performs, and exactly what used to crash."""
    monkeypatch.setattr(settings, "VOICE_DISABLED", False)

    vm = VoiceManager()
    detector = _FakeDetector()
    monkeypatch.setattr(
        "jarvis_engine.voice.voice_manager.WakeWordDetector",
        lambda **kwargs: detector,
    )
    # Keep the Whisper loader off the network: faster_whisper is imported
    # inside _load_whisper, so patch the module attribute it resolves.
    import faster_whisper

    def _fake_whisper(*args, **kwargs):
        raise RuntimeError("whisper load stubbed out in tests")

    monkeypatch.setattr(faster_whisper, "WhisperModel", _fake_whisper)

    vm.initialize(lambda *a, **k: None)
    assert len(vm._loader_threads) == 2

    vm.shutdown()

    assert all(not t.is_alive() for t in vm._loader_threads)
    assert vm.wake_word_detector is None
    assert detector.started, "the loader should have reached start()"
    assert detector.stopped, "shutdown must stop a detector the loader started"


def test_await_loaders_returns_true_when_nothing_is_running():
    vm = VoiceManager()
    assert vm._await_loaders() is True
    assert vm._loader_threads == []


def test_await_loaders_is_bounded_and_does_not_hang():
    """A loader that never finishes must not wedge shutdown forever -
    that would trade a crash for a hang."""
    vm = VoiceManager()
    stop = threading.Event()
    t = threading.Thread(target=stop.wait, daemon=True, name="stuck-loader")
    vm._loader_threads = [t]
    t.start()

    t0 = time.time()
    result = vm._await_loaders(timeout=0.3)
    elapsed = time.time() - t0

    assert result is False, "should report that a loader outlived the timeout"
    assert elapsed < 3.0, f"_await_loaders blocked for {elapsed:.1f}s"
    stop.set()


def test_await_loaders_survives_a_loader_that_raised():
    """The Events are only set on the success path, so a crashed loader
    would hang a wait() on them. join() must be used instead."""
    vm = VoiceManager()

    def boom():
        raise RuntimeError("wake word model missing")

    t = threading.Thread(target=boom, daemon=True, name="doomed-loader")
    vm._loader_threads = [t]
    t.start()

    assert vm._await_loaders(timeout=2.0) is True
    assert not vm.wake_word_ready.is_set()


def test_voice_disabled_skips_loader_threads_entirely(monkeypatch):
    """What keeps the suite off HuggingFace and off the microphone."""
    monkeypatch.setattr(settings, "VOICE_DISABLED", True)
    vm = VoiceManager()

    vm.initialize(lambda *a, **k: None)

    assert vm._loader_threads == []
    assert vm._initialized is False
    # The handler is still wired up - only model loading is skipped.
    assert vm.on_transcription is not None


def test_conftest_actually_disabled_voice_for_this_run():
    """Guards the fixture itself: if this flips back to False the suite
    silently starts downloading models and opening the mic again."""
    assert settings.VOICE_DISABLED is True


class _FakeDetector:
    """Stands in for WakeWordDetector: records whether the loader got as
    far as start(), and whether shutdown then stopped it."""

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True
