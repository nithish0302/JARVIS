"""Phrase-based interrupts (as opposed to the loudness-based barge-in in
wake_word.py): saying the wake phrase or a stop word mid-response must
interrupt TTS and NOT be sent downstream as a literal command."""

import threading
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from jarvis_engine.voice.voice_manager import VoiceManager, match_interrupt_phrase

# --- match_interrupt_phrase: pure matching logic -----------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("wake up jarvis", "wake"),
        ("Wake Up Jarvis", "wake"),  # case-insensitive
        ("wake up jarvis.", "wake"),  # trailing punctuation stripped
        ("wake up jarvis wake up jarvis", "wake"),  # the doubled bug-report case
        ("stop", "stop"),
        ("Stop.", "stop"),
        ("stop please", "stop"),
        ("wait", "stop"),
        ("wait a second", "stop"),
        ("cancel", "stop"),
        ("never mind", "stop"),
        ("hold on", "stop"),
    ],
)
def test_matches_interrupt_phrases(text, expected):
    assert match_interrupt_phrase(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "what time is it",
        "open notepad",
        "stopwatch",  # "stop" prefix but not a word boundary
        "waiting for the bus",  # "wait" prefix but not a word boundary
        "wakeboarding is fun",  # not the wake phrase
        "",
    ],
)
def test_normal_commands_are_not_interrupts(text):
    assert match_interrupt_phrase(text) is None


# --- _process_voice_command: end-to-end interrupt handling --------------


def _make_manager(transcribed_text: str, on_transcription=None) -> VoiceManager:
    vm = VoiceManager()
    vm.on_transcription = on_transcription
    vm.speech_recorder = MagicMock()
    vm.speech_recorder.record.return_value = np.ones(1600, dtype=np.float32)
    vm._transcribe = MagicMock(return_value=transcribed_text)
    return vm


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_wake_phrase_interrupt_stops_tts_and_starts_fresh_cycle(mock_tts):
    """Saying "wake up jarvis" mid-response must stop current playback,
    NOT be sent to on_transcription as a command, and start a genuinely
    new cycle (is_listening stays True throughout, not clobbered False)."""
    mock_tts.is_speaking = True
    on_transcription = MagicMock()
    vm = _make_manager("wake up jarvis", on_transcription)

    # Prevent the fresh cycle from actually spawning more threads/audio -
    # only care that it's invoked.
    vm._start_listening_cycle = MagicMock()
    vm.is_listening = True

    vm._process_voice_command(threading.Event())

    mock_tts.stop.assert_called_once()
    on_transcription.assert_not_called()
    vm._start_listening_cycle.assert_called_once()
    # The interrupt path must NOT reset is_listening to False itself -
    # that's _start_listening_cycle's job (mocked away here), so it should
    # still read True (never touched after the initial True).
    assert vm.is_listening is True


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_stop_phrase_interrupt_stops_and_returns_to_idle(mock_tts):
    """Saying "stop"/"wait"/etc must stop playback, NOT be sent to
    on_transcription, and NOT start a new "Yes sir?" cycle."""
    mock_tts.is_speaking = True
    on_transcription = MagicMock()
    vm = _make_manager("stop", on_transcription)
    vm._start_listening_cycle = MagicMock()
    vm.is_listening = True

    vm._process_voice_command(threading.Event())

    mock_tts.stop.assert_called_once()
    on_transcription.assert_not_called()
    vm._start_listening_cycle.assert_not_called()
    # No re-arm -> the finally block resets it back to False.
    assert vm.is_listening is False


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_interrupt_skips_stop_when_nothing_is_speaking(mock_tts):
    """If TTS isn't actually playing, don't call stop() needlessly - still
    must not send the interrupt phrase downstream as a command though."""
    mock_tts.is_speaking = False
    on_transcription = MagicMock()
    vm = _make_manager("wait", on_transcription)
    vm._start_listening_cycle = MagicMock()

    vm._process_voice_command(threading.Event())

    mock_tts.stop.assert_not_called()
    on_transcription.assert_not_called()


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_normal_command_during_open_recording_window_still_works(mock_tts):
    """Regression check: an ordinary command (not an interrupt phrase)
    must still reach on_transcription exactly as before."""
    mock_tts.is_speaking = True
    on_transcription = MagicMock()
    vm = _make_manager("what time is it", on_transcription)

    vm._process_voice_command(threading.Event())

    mock_tts.stop.assert_not_called()
    on_transcription.assert_called_once()
    call_text, call_direct_result = on_transcription.call_args[0]
    assert call_text == "what time is it"
    # "what time is it" is a direct VOICE_COMMAND_MAP match, so it should
    # be handled locally (non-None direct_result), not routed to the LLM.
    assert call_direct_result is not None
