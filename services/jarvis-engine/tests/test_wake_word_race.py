import time
import threading
import numpy as np
import pytest
from unittest.mock import MagicMock
from jarvis_engine.core.config import settings
from jarvis_engine.voice.wake_word import WakeWordDetector

def test_wake_word_toctou_race_prevented():
    """Simulate rapid, consecutive audio callbacks with high wake-word scores
    arriving in quick succession (every 80ms) while on_detected is executing.
    Confirms exactly 1 thread is dispatched, preventing duplicate spawns."""
    
    detection_count = 0
    detection_lock = threading.Lock()
    is_listening = False

    def get_is_listening():
        nonlocal is_listening
        return is_listening

    def set_is_listening(val):
        nonlocal is_listening
        is_listening = val

    def on_detected():
        nonlocal detection_count
        with detection_lock:
            detection_count += 1
        # Simulate processing time (recording & transcription)
        time.sleep(0.1)
        set_is_listening(False)

    detector = WakeWordDetector.__new__(WakeWordDetector)
    detector.model_path = "mock.onnx"
    detector.on_detected = on_detected
    detector.threshold = 0.3
    detector.sample_rate = 16000
    detector.chunk_size = 1280
    detector.is_running = True
    detector.get_is_listening = get_is_listening
    detector.set_is_listening = set_is_listening
    detector._detection_lock = threading.Lock()
    detector.tts_mute_buffer_seconds = 0.0  # mute gate not under test here
    detector.get_tts_state = lambda: (False, 0.0)  # never muted; avoids importing the TTS singleton
    detector._muted = False
    detector._flushing = False
    detector.last_detection_time = 0.0
    detector.score_log_floor = settings.WAKE_WORD_SCORE_LOG_FLOOR
    detector.cooldown_seconds = 0.05  # Short cooldown for this test

    mock_model = MagicMock()
    mock_model.predict.return_value = {"wake_up_jarvis": 0.95}
    detector.model = mock_model

    fake_audio = np.zeros((1280, 1), dtype=np.float32)

    # Fire 5 rapid audio callbacks consecutively
    for _ in range(5):
        detector._audio_callback(fake_audio, 1280, {}, None)

    # Wait for the single on_detected thread to finish
    time.sleep(0.15)

    assert detection_count == 1, f"Expected exactly 1 detection, got {detection_count}"

def test_wake_word_cooldown_rejection():
    """Verify that a second high-scoring audio chunk within the 2-second cooldown
    window is rejected, even if is_listening is False, and that after cooldown
    expires a new detection is allowed."""
    
    detection_count = 0
    is_listening = False

    def on_detected():
        nonlocal detection_count
        detection_count += 1

    detector = WakeWordDetector.__new__(WakeWordDetector)
    detector.model_path = "mock.onnx"
    detector.on_detected = on_detected
    detector.threshold = 0.3
    detector.sample_rate = 16000
    detector.chunk_size = 1280
    detector.is_running = True
    detector.get_is_listening = lambda: is_listening
    detector.set_is_listening = lambda val: None
    detector._detection_lock = threading.Lock()
    detector.tts_mute_buffer_seconds = 0.0  # mute gate not under test here
    detector.get_tts_state = lambda: (False, 0.0)  # never muted; avoids importing the TTS singleton
    detector._muted = False
    detector._flushing = False
    detector.last_detection_time = 0.0
    detector.score_log_floor = settings.WAKE_WORD_SCORE_LOG_FLOOR
    detector.cooldown_seconds = 0.3  # 300ms cooldown for test

    mock_model = MagicMock()
    mock_model.predict.return_value = {"wake_up_jarvis": 0.95}
    detector.model = mock_model

    fake_audio = np.zeros((1280, 1), dtype=np.float32)

    # 1. First detection at t=0
    detector._audio_callback(fake_audio, 1280, {}, None)
    time.sleep(0.05)
    assert detection_count == 1

    # 2. Immediate second utterance within 100ms (< 300ms cooldown) -> rejected
    detector._audio_callback(fake_audio, 1280, {}, None)
    time.sleep(0.05)
    assert detection_count == 1, "Cooldown failed to suppress second rapid trigger"

    # 3. Wait for cooldown to expire (> 300ms)
    time.sleep(0.3)

    # 4. Third utterance after cooldown -> accepted
    detector._audio_callback(fake_audio, 1280, {}, None)
    time.sleep(0.05)
    assert detection_count == 2, "Third utterance after cooldown should trigger"

def test_wake_word_10_sequential_utterances():
    """Simulate 10 consecutive wake word utterances with pauses between each,
    verifying exactly 1 detection per utterance and logging all timestamps."""
    
    detection_logs = []
    detection_lock = threading.Lock()
    is_listening = False

    def get_is_listening():
        nonlocal is_listening
        return is_listening

    def set_is_listening(val):
        nonlocal is_listening
        val_str = "listening" if val else "idle"
        is_listening = val

    def on_detected():
        with detection_lock:
            t = time.time()
            detection_logs.append(t)
        # Simulate processing cycle
        time.sleep(0.05)
        set_is_listening(False)

    detector = WakeWordDetector.__new__(WakeWordDetector)
    detector.model_path = "mock.onnx"
    detector.on_detected = on_detected
    detector.threshold = 0.3
    detector.sample_rate = 16000
    detector.chunk_size = 1280
    detector.is_running = True
    detector.get_is_listening = get_is_listening
    detector.set_is_listening = set_is_listening
    detector._detection_lock = threading.Lock()
    detector.tts_mute_buffer_seconds = 0.0  # mute gate not under test here
    detector.get_tts_state = lambda: (False, 0.0)  # never muted; avoids importing the TTS singleton
    detector._muted = False
    detector._flushing = False
    detector.last_detection_time = 0.0
    detector.score_log_floor = settings.WAKE_WORD_SCORE_LOG_FLOOR
    detector.cooldown_seconds = 0.1  # 100ms cooldown for fast test execution

    mock_model = MagicMock()
    mock_model.predict.return_value = {"wake_up_jarvis": 0.95}
    detector.model = mock_model

    fake_audio = np.zeros((1280, 1), dtype=np.float32)

    print("\n=== 10 SEQUENTIAL WAKE WORD UTTERANCES TEST ===")
    start_time = time.time()
    for i in range(1, 11):
        # Simulate multiple audio chunks per utterance
        for _ in range(3):
            detector._audio_callback(fake_audio, 1280, {}, None)
        
        # Natural pause between utterances (allows processing + cooldown)
        time.sleep(0.15)

    time.sleep(0.1)

    print(f"Total detections: {len(detection_logs)} / 10 expected")
    for idx, ts in enumerate(detection_logs, 1):
        rel_time = ts - start_time
        print(f"  Utterance #{idx:02d}: Detected at +{rel_time:.3f}s (epoch {ts:.3f})")

    assert len(detection_logs) == 10, f"Expected exactly 10 detections, got {len(detection_logs)}"
