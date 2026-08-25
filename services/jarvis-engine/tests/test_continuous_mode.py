"""Continuous conversation mode: after a wake-word session's first command
is answered, JARVIS keeps listening for follow-up commands directly (no
repeated "wake up jarvis") until an explicit exit phrase or a silence
timeout. See voice_manager.py's continue_conversation() /
_on_continuous_timeout() / match_continuous_exit_phrase() for the
implementation this exercises.

Every test builds a FRESH VoiceManager() (never the shared `voice_manager`
singleton) so state never leaks between tests or other test files - same
pattern as test_interrupt_phrases.py.
"""
import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from jarvis_engine.voice.voice_manager import VoiceManager, match_continuous_exit_phrase


# --- match_continuous_exit_phrase: pure matching logic -------------------

@pytest.mark.parametrize("text", [
    "stop listening jarvis",
    "Stop Listening Jarvis",  # case-insensitive
    "stop listening jarvis.",  # trailing punctuation
    "jarvis go to sleep",
    "Jarvis go to sleep.",
    "thats all jarvis",
    "that's all jarvis",  # apostrophe-insensitive
    "That's All Jarvis",
    "jarvis i will talk to you later",
    "Jarvis I Will Talk To You Later",
])
def test_matches_continuous_exit_phrases(text):
    assert match_continuous_exit_phrase(text) is True


@pytest.mark.parametrize("text", [
    "what time is it",
    "open notepad",
    "stop",  # an INTERRUPT phrase, not an exit phrase
    "wake up jarvis",
    "jarvis",
    "",
])
def test_normal_text_is_not_a_continuous_exit_phrase(text):
    assert match_continuous_exit_phrase(text) is False


# --- end-to-end: _process_voice_command while continuous_mode -----------

def _make_manager(audio_sequence, transcripts) -> VoiceManager:
    """audio_sequence: list of np arrays returned by successive
    speech_recorder.record() calls (last one repeats if exhausted).
    transcripts: list of strings returned by successive _transcribe() calls
    (only consulted for non-empty audio windows)."""
    vm = VoiceManager()
    vm.speech_recorder = MagicMock()
    vm.speech_recorder.record.side_effect = list(audio_sequence) + [audio_sequence[-1]] * 10
    vm._transcribe = MagicMock(side_effect=list(transcripts) + [transcripts[-1]] * 10)
    vm.on_transcription = MagicMock()
    return vm


NONEMPTY = np.ones(1600, dtype=np.float32)
EMPTY = np.array([])


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_exit_phrase_ends_continuous_mode(mock_tts):
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY], ["jarvis go to sleep"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    assert vm.continuous_mode is False
    vm.on_transcription.assert_not_called()
    # Closing acknowledgment spoken, then idle broadcast, then not listening.
    assert mock_tts.speak_sync.call_count == 1
    assert "sleep" in mock_tts.speak_sync.call_args[0][0].lower()
    assert vm.is_listening is False


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_exit_phrase_apostrophe_variant_also_matches(mock_tts):
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY], ["that's all jarvis"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    assert vm.continuous_mode is False
    vm.on_transcription.assert_not_called()


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_exit_phrase_cancels_the_armed_timer(mock_tts):
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY], ["stop listening jarvis"])
    vm.continuous_mode = True
    vm.is_listening = True
    # Simulate a timer already armed from a previous turn.
    vm._continuous_timer = MagicMock()
    stale_timer = vm._continuous_timer

    vm._process_voice_command(None)

    stale_timer.cancel.assert_called_once()
    assert vm._continuous_timer is None


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_redundant_wake_phrase_in_continuous_mode_is_ignored(mock_tts):
    """Saying "wake up jarvis" while already in continuous mode must NOT
    call on_transcription, NOT start a fresh "Yes sir?" cycle, and must
    NOT exit continuous mode - just keep listening."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY, NONEMPTY], ["wake up jarvis", "what time is it"])
    vm.continuous_mode = True
    vm.is_listening = True
    vm._start_listening_cycle = MagicMock()

    vm._process_voice_command(None)

    vm._start_listening_cycle.assert_not_called()
    assert vm.continuous_mode is True
    # No "Yes sir?"/acknowledgment spoken for the redundant wake word.
    mock_tts.speak_sync.assert_not_called()
    # It looped back and picked up the SECOND utterance as the real command.
    vm.on_transcription.assert_called_once()
    call_text, _ = vm.on_transcription.call_args[0]
    assert call_text == "what time is it"
    assert vm.speech_recorder.record.call_count == 2


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_stop_interrupt_in_continuous_mode_keeps_listening(mock_tts):
    """"stop"/"wait"/etc are NOT one of the 4 explicit exit phrases, so
    they must not silently end the conversation - only stop playback and
    keep listening for the next command."""
    mock_tts.is_speaking = True
    vm = _make_manager([NONEMPTY, NONEMPTY], ["stop", "open notepad"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    mock_tts.stop.assert_called_once()
    assert vm.continuous_mode is True
    vm.on_transcription.assert_called_once()
    assert vm.speech_recorder.record.call_count == 2


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_no_speech_window_loops_without_exiting_or_resetting_timer(mock_tts):
    """A per-window "no speech" timeout must NOT reset the session timer
    and must NOT exit continuous mode by itself - only the session-level
    timer (or an exit phrase) does that."""
    mock_tts.is_speaking = False
    # Only ONE non-empty window here, so _transcribe (only ever called for
    # non-empty audio) is only ever called once too.
    vm = _make_manager([EMPTY, EMPTY, NONEMPTY], ["open notepad"])
    vm.continuous_mode = True
    vm.is_listening = True
    vm._continuous_timer_token = 5  # sentinel: must stay untouched by "no speech"

    vm._process_voice_command(None)

    assert vm.continuous_mode is True
    assert vm.speech_recorder.record.call_count == 3
    vm.on_transcription.assert_called_once()
    # Only the FINAL, real-speech window armed/re-armed the timer - the two
    # empty windows before it must not have touched the token.
    assert vm._continuous_timer_token == 6


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_normal_command_in_continuous_mode_resets_is_listening_false(mock_tts):
    """A dispatched command still goes idle-in-between (is_listening False)
    until continue_conversation() reopens the mic once the response is
    spoken - unchanged from the non-continuous behavior."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY], ["open notepad"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    vm.on_transcription.assert_called_once()
    assert vm.is_listening is False
    assert vm.continuous_mode is True  # conversation isn't over, just paused


# --- continue_conversation(): entering / re-arming continuous mode -------

def test_continue_conversation_enters_continuous_mode_and_opens_mic():
    vm = VoiceManager()
    vm.speech_recorder = MagicMock()
    vm.speech_recorder.record.return_value = np.array([])  # window comes back empty; keep it simple
    assert vm.continuous_mode is False

    vm.continue_conversation()

    assert vm.continuous_mode is True
    assert vm.is_listening is True
    assert vm._continuous_timer is not None

    # Give the spawned recording thread a moment to run and settle.
    deadline = time.time() + 2.0
    while vm.speech_recorder.record.call_count == 0 and time.time() < deadline:
        time.sleep(0.01)
    assert vm.speech_recorder.record.call_count >= 1

    vm.shutdown()


def test_continue_conversation_broadcasts_continuous_status():
    vm = VoiceManager()
    vm.speech_recorder = MagicMock()
    vm.speech_recorder.record.return_value = np.array([])
    vm._broadcast_status = MagicMock()

    vm.continue_conversation()

    vm._broadcast_status.assert_called_once_with("continuous")
    vm.shutdown()


# --- session-level silence timer -----------------------------------------

@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_timeout_fires_exits_continuous_mode_and_speaks_ack(mock_tts):
    vm = VoiceManager()
    vm.continuous_mode = True
    vm._continuous_timer_token = 1
    vm._broadcast_status = MagicMock()

    vm._on_continuous_timeout(1)

    assert vm.continuous_mode is False
    assert vm.is_listening is False
    mock_tts.speak_sync.assert_called_once()
    assert "sleep" in mock_tts.speak_sync.call_args[0][0].lower()
    vm._broadcast_status.assert_any_call("idle")


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_stale_timeout_token_is_a_no_op(mock_tts):
    """A timer that fires after being superseded (real speech reset it, or
    a fresh session already started) must do nothing."""
    vm = VoiceManager()
    vm.continuous_mode = True
    vm._continuous_timer_token = 2  # a newer arm already happened

    vm._on_continuous_timeout(1)  # stale token

    assert vm.continuous_mode is True  # untouched
    mock_tts.speak_sync.assert_not_called()


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_timeout_when_already_not_continuous_is_a_no_op(mock_tts):
    vm = VoiceManager()
    vm.continuous_mode = False
    vm._continuous_timer_token = 1

    vm._on_continuous_timeout(1)

    mock_tts.speak_sync.assert_not_called()


def test_real_speech_rearms_timer_cancelling_the_previous_one():
    vm = VoiceManager()
    vm.continuous_mode = True
    first_timer = MagicMock()
    vm._continuous_timer = first_timer
    vm._continuous_timer_token = 1

    with vm._continuous_lock:
        vm._arm_continuous_timer()

    first_timer.cancel.assert_called_once()
    assert vm._continuous_timer_token == 2
    assert vm._continuous_timer is not first_timer
    vm._cancel_continuous_timer()


# --- shutdown() must never leak the timer/state ---------------------------

def test_shutdown_cancels_continuous_timer_and_resets_state():
    vm = VoiceManager()
    vm.continuous_mode = True
    with vm._continuous_lock:
        vm._arm_continuous_timer()
    timer = vm._continuous_timer
    assert timer is not None

    vm.shutdown()

    assert vm.continuous_mode is False
    assert vm._continuous_timer is None
    assert timer.finished.is_set() or not timer.is_alive()
