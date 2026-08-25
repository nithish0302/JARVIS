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

from jarvis_engine.voice.voice_manager import (
    VoiceManager,
    match_continuous_exit_phrase,
    _looks_like_uncertain_exit_intent,
    _is_affirmative,
)


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
    # Bare variants without "jarvis" attached - CONFIRMED INCIDENT: "Go to
    # sleep." (no wake word) matched nothing and reached the LLM, which
    # fabricated a fake "session ended" response.
    "go to sleep",
    "Go to sleep.",
    "stop listening",
    "Stop Listening.",
    "thats all",
    "that's all",
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


# --- _looks_like_uncertain_exit_intent / _is_affirmative: the second,
# phrase-list-independent defense layer -----------------------------------

@pytest.mark.parametrize("text", [
    "sleep",
    "I need sleep",
    "shut down",
    "power down",
    "im done",
    "I'm done",
    "thats enough",
    "that's enough",
])
def test_uncertain_exit_intent_matches_short_sleep_stop_phrases(text):
    assert _looks_like_uncertain_exit_intent(text) is True


@pytest.mark.parametrize("text", [
    "what time is it",
    "open notepad",
    "what's the nearest bus stop",  # contains "stop" but NOT "stop listening"
    "how do I get more sleep at night without waking up early",  # "sleep" present but > 6 words
    "",
    "hello",
])
def test_uncertain_exit_intent_does_not_false_positive(text):
    assert _looks_like_uncertain_exit_intent(text) is False


@pytest.mark.parametrize("text", [
    "yes", "Yes.", "yeah", "yep", "yup", "correct", "please",
    "affirmative", "do it", "please do", "thats right", "right", "go ahead",
    "yes please",  # word-boundary prefix match, same style as other phrase checks
])
def test_is_affirmative_matches_clear_yes(text):
    assert _is_affirmative(text) is True


@pytest.mark.parametrize("text", [
    "no", "what time is it", "open notepad", "", "maybe", "not really",
])
def test_is_affirmative_rejects_anything_else(text):
    assert _is_affirmative(text) is False


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
    # These tests call _process_voice_command directly/synchronously (no
    # continue_conversation() running concurrently to ever signal
    # _continuous_turn_ready), so a dispatched normal command would
    # otherwise block on the real 120s default - keep it near-instant.
    vm._continuous_turn_wait_timeout = 0.05
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
def test_bare_go_to_sleep_ends_session_with_no_llm_involvement(mock_tts):
    """CONFIRMED INCIDENT regression check: "go to sleep" with no "jarvis"
    must now end the session directly - never reach on_transcription (the
    LLM path), which previously fabricated a fake "session ended" reply."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY], ["go to sleep"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    assert vm.continuous_mode is False
    vm.on_transcription.assert_not_called()
    assert "sleep" in mock_tts.speak_sync.call_args[0][0].lower()


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_uncertain_exit_intent_asks_deterministic_confirmation_not_llm(mock_tts):
    """An exit-*sounding* phrase that ISN'T in the configured list (e.g. a
    phrasing variant CONTINUOUS_MODE_EXIT_PHRASES doesn't cover) must never
    reach execute_voice_command/on_transcription - it gets a hardcoded
    confirmation question instead. The session's single persistent thread
    loops straight back to record the answer (same pattern as the
    pre-existing "Didn't catch that, sir." branch) all within this one
    _process_voice_command call - the second turn here is an ordinary
    non-affirmative reply, just so the call terminates naturally via the
    normal dispatch return path."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY, NONEMPTY], ["I think I should sleep now", "no thanks"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    # The uncertain phrase itself never reached the LLM - only the
    # (non-affirmative) reply to the confirmation question did, once it
    # fell through as an ordinary command.
    vm.on_transcription.assert_called_once()
    call_text, _ = vm.on_transcription.call_args[0]
    assert call_text == "no thanks"

    # The confirmation question was spoken deterministically, first.
    first_spoken = mock_tts.speak_sync.call_args_list[0][0][0].lower()
    assert "stop listening" in first_spoken
    assert vm.continuous_mode is True  # never actually exited


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_confirmation_answered_yes_performs_real_exit(mock_tts):
    """The exit only actually happens once "yes" is heard - backed by the
    same continuous_mode=False / timer-cancel / _exit_continuous_mode()
    state change as every other exit path, not an LLM-generated claim."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY, NONEMPTY], ["I think I should sleep now", "yes"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    assert vm.continuous_mode is False
    assert vm._pending_exit_confirmation is False
    vm.on_transcription.assert_not_called()
    assert mock_tts.speak_sync.call_count == 2
    assert "stop listening" in mock_tts.speak_sync.call_args_list[0][0][0].lower()
    assert "sleep" in mock_tts.speak_sync.call_args_list[1][0][0].lower()


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_confirmation_answered_with_something_else_is_treated_as_a_command(mock_tts):
    """If the "answer" isn't a clear yes, it must NOT be silently discarded
    - it's processed as this turn's actual command instead."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY, NONEMPTY], ["I think I should sleep now", "open notepad"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    assert vm._pending_exit_confirmation is False
    assert vm.continuous_mode is True  # NOT exited - "open notepad" wasn't a yes
    vm.on_transcription.assert_called_once()
    call_text, _ = vm.on_transcription.call_args[0]
    assert call_text == "open notepad"


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_unrelated_command_with_stop_substring_reaches_llm_normally(mock_tts):
    """False-positive guard: a normal command that happens to contain
    "stop" in an unrelated context (not "stop listening") must go straight
    to on_transcription like any other command, no confirmation asked."""
    mock_tts.is_speaking = False
    vm = _make_manager([NONEMPTY], ["what's the nearest bus stop"])
    vm.continuous_mode = True
    vm.is_listening = True

    vm._process_voice_command(None)

    assert vm._pending_exit_confirmation is False
    assert vm.continuous_mode is True
    mock_tts.speak_sync.assert_not_called()
    vm.on_transcription.assert_called_once()
    call_text, _ = vm.on_transcription.call_args[0]
    assert call_text == "what's the nearest bus stop"


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


def test_continue_conversation_spawns_thread_exactly_once_per_session():
    """Regression test: continue_conversation() used to spawn a brand new
    thread on EVERY call (once per turn), racing the session's own
    already-alive recording thread (duplicate recordings, exit phrases
    only working intermittently). Only the FIRST call (entering continuous
    mode) may spawn a thread - every later call in the same session must
    only re-arm the timer and signal the existing thread.

    Patching threading.Thread itself isn't safe here - Timer subclasses
    Thread, and _arm_continuous_timer() (called by every
    continue_conversation() call) constructs one, so mocking Thread
    globally breaks Timer's own __init__. Track spawns by wrapping the
    thread's target callable instead."""
    vm = VoiceManager()
    spawn_count = {"n": 0}

    def counting_target(*args, **kwargs):
        spawn_count["n"] += 1
        # No real recording loop needed for this test - just prove it ran.

    vm._process_voice_command = counting_target

    vm.continue_conversation()  # first entry: should spawn
    vm.continue_conversation()  # same session: must NOT spawn again
    vm.continue_conversation()  # same session: must NOT spawn again

    # Give the one legitimate spawned thread a moment to actually run.
    deadline = time.time() + 2.0
    while spawn_count["n"] == 0 and time.time() < deadline:
        time.sleep(0.01)

    assert spawn_count["n"] == 1
    assert vm.continuous_mode is True
    vm.shutdown()


def test_continue_conversation_signals_existing_thread_on_later_calls():
    """The second+ call must wake the already-waiting thread instead of
    spawning a new one."""
    vm = VoiceManager()
    vm._process_voice_command = MagicMock()

    vm.continue_conversation()  # spawns the (mocked-away) thread
    assert not vm._continuous_turn_ready.is_set()

    vm.continue_conversation()  # re-arm: should signal it

    assert vm._continuous_turn_ready.is_set()


@patch("jarvis_engine.voice.tts_engine.tts_engine")
def test_five_real_turns_run_on_a_single_thread_with_no_duplicate_recordings(mock_tts):
    """End-to-end regression check for the actual reported bug: 5
    back-to-back turns, each simulating continue_conversation() being
    called once its (mocked) response has been spoken - exactly like
    transcription_handler._speak_response does in production. Must use
    the SAME thread throughout (real _process_voice_command only ever
    invoked once) and record/transcribe exactly once per turn - no
    duplicates from a second competing thread."""
    mock_tts.is_speaking = False
    vm = VoiceManager()
    vm.speech_recorder = MagicMock()
    vm.speech_recorder.record.return_value = NONEMPTY
    vm._transcribe = MagicMock(side_effect=[
        "open notepad", "what time is it", "volume up", "lock screen", "mute",
    ])
    vm.on_transcription = MagicMock()
    vm._continuous_turn_wait_timeout = 2.0
    # _broadcast_status does a real (localhost, but still real) HTTP POST -
    # nothing is listening on it in this test process, and depending on
    # the environment that can take close to its own timeout to fail
    # rather than failing instantly, which was silently eating into this
    # test's own polling budgets below. Mock it out like the other
    # broadcast-focused tests in this file already do.
    vm._broadcast_status = MagicMock()

    spawn_count = {"n": 0}
    real_target = vm._process_voice_command

    def counting_target(*args, **kwargs):
        spawn_count["n"] += 1
        return real_target(*args, **kwargs)

    vm._process_voice_command = counting_target

    def wait_for(predicate, timeout=2.0):
        deadline = time.time() + timeout
        while not predicate() and time.time() < deadline:
            time.sleep(0.01)
        assert predicate(), "condition not met before timeout"

    # Turn 1's "response spoken" -> enters continuous mode, spawns the
    # session's one thread, which immediately records+dispatches turn 2.
    vm.continue_conversation()

    for turn in range(2, 6):
        wait_for(lambda t=turn: vm.on_transcription.call_count >= t - 1)
        # Simulate that turn's response finishing speaking, exactly as
        # _speak_response's finally block does.
        vm.continue_conversation()

    wait_for(lambda: vm.on_transcription.call_count >= 5)

    assert vm.on_transcription.call_count == 5
    assert vm.speech_recorder.record.call_count == 5
    assert vm._transcribe.call_count == 5
    # The one and only thing that matters for the reported bug: exactly
    # ONE thread ever ran _process_voice_command for this whole session.
    assert spawn_count["n"] == 1

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
