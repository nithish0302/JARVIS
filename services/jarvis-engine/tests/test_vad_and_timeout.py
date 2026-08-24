import time
import threading
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from jarvis_engine.voice.speech_recorder import SpeechRecorder

def test_speech_recorder_pause_before_speaking():
    """Test that pre-speech silence (e.g. 2.5s pause) does NOT trigger early cutoff.
    Speech begins at 2.5s and continues until trailing silence."""
    
    recorder = SpeechRecorder(
        sample_rate=16000,
        silence_threshold=0.01,
        silence_duration=1.5,
        wait_for_speech_timeout=6.0,
        max_duration=30.0
    )

    # 1024 samples @ 16kHz is 64ms per chunk (15.625 chunks/sec)
    # Generate 2.5s of silence (39 chunks of 0.001 RMS)
    # followed by 1.5s of speech (24 chunks of 0.05 RMS)
    # followed by 1.5s of trailing silence (24 chunks of 0.001 RMS)
    silence_chunk = np.full((1024, 1), 0.001, dtype=np.float32)
    speech_chunk = np.full((1024, 1), 0.05, dtype=np.float32)

    chunks = ([silence_chunk] * 40) + ([speech_chunk] * 25) + ([silence_chunk] * 30)
    chunk_iter = iter(chunks)

    mock_stream = MagicMock()
    mock_stream.read.side_effect = lambda size: (next(chunk_iter, silence_chunk), None)

    with patch("sounddevice.InputStream") as mock_input_stream:
        mock_input_stream.return_value.__enter__.return_value = mock_stream
        
        audio = recorder.record()

    # Total recorded chunks: 40 (pre-speech) + 25 (speech) + ~23 (trailing silence) ~ 88 chunks
    # 88 * 1024 / 16000 = 5.6s
    assert len(audio) > 0, "Recording should not be empty"
    recorded_duration = len(audio) / 16000
    print(f"\n[TEST 1] Pre-speech 2.5s pause recorded total: {recorded_duration:.2f}s")
    assert recorded_duration > 4.0, f"Expected recording > 4.0s including speech, got {recorded_duration:.2f}s"

def test_speech_recorder_no_speech_timeout():
    """Test that 6+ seconds of continuous silence terminates with no speech detected."""
    
    recorder = SpeechRecorder(
        sample_rate=16000,
        silence_threshold=0.01,
        silence_duration=1.5,
        wait_for_speech_timeout=6.0,
        max_duration=30.0
    )

    silence_chunk = np.full((1024, 1), 0.001, dtype=np.float32)
    
    mock_stream = MagicMock()
    mock_stream.read.return_value = (silence_chunk, None)

    with patch("sounddevice.InputStream") as mock_input_stream:
        mock_input_stream.return_value.__enter__.return_value = mock_stream
        
        audio = recorder.record()

    print(f"\n[TEST 2] Continuous silence returned audio length: {len(audio)}")
    assert len(audio) == 0, "Continuous silence should return empty array"

def test_speech_recorder_timeout_anchors_to_tts_finished_event():
    """wait_for_speech_timeout must not start counting down until
    tts_finished_event is set (real 'Yes sir?' playback completion) - not
    from whenever record() happened to be called. A slow TTS call should
    not silently eat into the user's real window to respond."""

    recorder = SpeechRecorder(
        sample_rate=16000,
        silence_threshold=0.01,
        silence_duration=1.5,
        wait_for_speech_timeout=6.0,
        max_duration=30.0
    )

    silence_chunk = np.full((1024, 1), 0.001, dtype=np.float32)
    event = threading.Event()  # unset = TTS still speaking

    call_count = {"n": 0}
    # Old frame-count-from-record-start behavior would give up after ~93
    # chunks (6s @ 15.625 chunks/sec). Simulate a slow TTS call still
    # playing well past that point before "finishing".
    tts_finish_at_call = 150

    def read_side_effect(size):
        call_count["n"] += 1
        if call_count["n"] == tts_finish_at_call:
            event.set()
        return (silence_chunk, None)

    mock_stream = MagicMock()
    mock_stream.read.side_effect = read_side_effect

    with patch("sounddevice.InputStream") as mock_input_stream:
        mock_input_stream.return_value.__enter__.return_value = mock_stream
        audio = recorder.record(tts_finished_event=event)

    assert len(audio) == 0, "Should still give up once TTS is done and 6s of silence passes"

    # The call that flips the event also counts as the first post-TTS wait
    # frame (the event is already set by the time this method checks it),
    # so the give-up call is tts_finish_at_call + max_wait_frames - 1.
    max_wait_frames = int(6.0 * (16000 // 1024))
    assert call_count["n"] >= tts_finish_at_call + max_wait_frames - 1, (
        f"Timeout fired before the post-TTS-completion countdown elapsed: "
        f"{call_count['n']} calls"
    )
    # And well past where the OLD from-record-start counting would have
    # given up (~max_wait_frames calls in) - proving the clock really did
    # wait for TTS completion rather than starting immediately.
    assert call_count["n"] > max_wait_frames + 50


def test_empty_transcription_feedback():
    """Test that empty audio or empty transcription correctly triggers fallback
    status broadcasts and does not leave the pipeline hanging."""
    from jarvis_engine.voice.voice_manager import voice_manager
    
    mock_recorder = MagicMock()
    mock_recorder.record.return_value = np.array([])
    
    original_recorder = voice_manager.speech_recorder
    voice_manager.speech_recorder = mock_recorder

    with patch("requests.post") as mock_post:
        # Simulate wake word detected with no speech
        voice_manager._on_wake_word_detected()
        time.sleep(0.1)

    voice_manager.speech_recorder = original_recorder
    assert not voice_manager.is_listening, "is_listening should be False after cycle"
