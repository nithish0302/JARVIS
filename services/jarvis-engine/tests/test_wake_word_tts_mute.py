"""Regression tests for the wake-word TTS mute gate (BUG B).

JARVIS's own TTS output was reaching the openWakeWord model through the
mic and producing genuine high-confidence (0.99+) detections, so the
assistant re-triggered itself in an endless loop with no user input.

The gate must:
  - run ZERO predictions while TTS is speaking,
  - stay muted for a configurable buffer after speech ends (echo tail),
  - resume afterwards,
  - and never suppress legitimate repeated user wake words.
"""

import threading
import time

import numpy as np

from jarvis_engine.core.config import settings
from jarvis_engine.voice.wake_word import WakeWordDetector


class FakeModel:
    """Records every predict() call so we can assert it never sees our audio."""

    def __init__(self, score=0.0):
        self.score = score
        self.calls = 0

    def predict(self, audio):
        self.calls += 1
        return {"wake_up_jarvis": self.score}

    def reset(self):
        pass


class TTSState:
    """Stand-in for the tts_engine singleton's speaking state."""

    def __init__(self):
        self.is_speaking = False
        self.last_speech_end_time = 0.0

    def stop_speaking(self):
        self.is_speaking = False
        self.last_speech_end_time = time.time()

    def as_callable(self):
        return lambda: (self.is_speaking, self.last_speech_end_time)


def make_detector(model, tts: TTSState, buffer_seconds, on_detected=None):
    d = WakeWordDetector.__new__(WakeWordDetector)
    d.model = model
    d.model_path = "mock.onnx"
    d.on_detected = on_detected or (lambda: None)
    d.threshold = 0.3
    d.sample_rate = 16000
    d.chunk_size = 1280
    d.is_running = True
    d.get_is_listening = lambda: False
    d.set_is_listening = None
    d._detection_lock = threading.Lock()
    d.last_detection_time = 0.0
    d.cooldown_seconds = 0.0
    d.score_log_floor = settings.WAKE_WORD_SCORE_LOG_FLOOR
    d.tts_mute_buffer_seconds = buffer_seconds
    d.get_tts_state = tts.as_callable()
    d._muted = False
    d._flushing = False
    return d


# Quiet frame: below the 0.08 interrupt-heuristic threshold, so these tests
# exercise the mute gate specifically and not the barge-in path.
QUIET_FRAME = np.full((1280, 1), 0.01, dtype=np.float32)


def test_predictions_run_when_tts_silent():
    model = FakeModel()
    d = make_detector(model, TTSState(), 0.4)

    for _ in range(5):
        d._audio_callback(QUIET_FRAME, 1280, None, None)

    assert model.calls == 5


def test_own_audio_never_reaches_the_model_while_speaking():
    model = FakeModel()
    tts = TTSState()
    d = make_detector(model, tts, 0.4)

    tts.is_speaking = True
    for _ in range(20):
        d._audio_callback(QUIET_FRAME, 1280, None, None)

    assert model.calls == 0, "JARVIS's own audio was fed to the wake-word model"


def test_still_muted_during_buffer_after_speech_ends():
    model = FakeModel()
    tts = TTSState()
    d = make_detector(model, tts, 0.4)

    tts.is_speaking = True
    d._audio_callback(QUIET_FRAME, 1280, None, None)
    tts.stop_speaking()

    for _ in range(5):
        d._audio_callback(QUIET_FRAME, 1280, None, None)

    assert model.calls == 0, "resumed during the echo-tail buffer"


def test_resumes_after_buffer_expires():
    model = FakeModel()
    tts = TTSState()
    buffer_seconds = 0.2
    d = make_detector(model, tts, buffer_seconds)

    tts.is_speaking = True
    d._audio_callback(QUIET_FRAME, 1280, None, None)
    tts.stop_speaking()

    time.sleep(buffer_seconds + 0.1)

    # First unmuted frame triggers the stale-buffer flush.
    d._audio_callback(QUIET_FRAME, 1280, None, None)
    deadline = time.time() + 2
    while d._flushing and time.time() < deadline:
        time.sleep(0.01)
    assert not d._flushing, "buffer flush did not complete"

    model.calls = 0
    for _ in range(5):
        d._audio_callback(QUIET_FRAME, 1280, None, None)

    assert model.calls == 5, "did not resume predicting after the buffer expired"


def test_legitimate_repeated_wake_words_not_suppressed():
    """The gate must only suppress JARVIS's own audio, never real users."""
    fires = []
    model = FakeModel(score=0.99)
    tts = TTSState()  # never speaking
    d = make_detector(model, tts, 0.4, on_detected=lambda: fires.append(time.time()))

    for _ in range(3):
        d._audio_callback(QUIET_FRAME, 1280, None, None)
        time.sleep(0.3)
    time.sleep(0.3)

    assert len(fires) == 3, f"suppressed legitimate wake words: {len(fires)}/3"


def test_mute_buffer_is_configurable_not_hardcoded():
    assert hasattr(settings, "WAKE_WORD_TTS_MUTE_BUFFER_SECONDS")
    assert settings.WAKE_WORD_TTS_MUTE_BUFFER_SECONDS > 0

    model = FakeModel()
    tts = TTSState()
    d = make_detector(model, tts, settings.WAKE_WORD_TTS_MUTE_BUFFER_SECONDS)
    assert d.tts_mute_buffer_seconds == settings.WAKE_WORD_TTS_MUTE_BUFFER_SECONDS
