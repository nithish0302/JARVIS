"""Shared voice-transcription handler.

This lives in its own module (rather than as a closure inside main.py's
lifespan) so that BOTH the startup path and the POST /voice/start route
register the exact same handler. Previously /voice/start installed a
1-argument stub that clobbered the real handler, causing every real
transcription to die with:

    on_transcription() takes 1 positional argument but 2 were given

The signature is (text, direct_result=None) to match the call site in
voice_manager.process_voice():

  - direct_result is not None -> the command was already executed locally
    by execute_voice_command(); the string is its response. We broadcast
    it to the UI as direct_response and speak it. No LLM round-trip.
  - direct_result is None     -> no direct command matched; POST the text
    to /voice/input and let the LLM pipeline produce the response, then
    speak that.
"""

import re
import threading

from ..core.utils import safe_print

VOICE_INPUT_URL = "http://localhost:8765/voice/input"
VOICE_STATUS_URL = "http://localhost:8765/voice/status/update"


def clean_text_for_tts(text: str) -> str:
    """Strip UI_ACTION tags and markdown formatting for clean TTS output"""
    if not text:
        return ""

    # Strip UI_ACTION tags
    clean = re.sub(r"\[UI_ACTION:[^\]]*\]", "", text).strip()

    # Strip markdown formatting
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)  # Bold
    clean = re.sub(r"\*(.+?)\*", r"\1", clean)  # Italic
    clean = re.sub(r"#{1,6}\s", "", clean)  # Headers
    clean = re.sub(r"`(.+?)`", r"\1", clean)  # Inline code
    clean = re.sub(r"```[\s\S]*?```", "", clean)  # Code blocks

    return clean.strip()


def _post_status(status: str, timeout: int = 2):
    import requests

    try:
        requests.post(VOICE_STATUS_URL, json={"status": status}, timeout=timeout)
    except Exception:
        pass


def _speak_response(response_text: str):
    """Speak a response through TTS, bracketing it with speaking/idle
    status broadcasts so the orb stays in sync.

    The "speaking" broadcast fires from on_speech_start, which tts_engine
    invokes the instant is_speaking flips False -> True - i.e. the moment
    audio actually starts playing, not when speak_sync() is called (which
    can precede audible Kokoro audio by 1-3+ seconds of warmup/TTFB).

    Once the response has genuinely finished speaking, hands off to
    continuous conversation mode (voice_manager.continue_conversation())
    instead of just going idle - this is the ONLY caller of that method,
    since it's the one place shared by both the direct-command and LLM
    voice paths (see handle_transcription below). continue_conversation()
    broadcasts its own status ("continuous"), so this does not also
    broadcast "idle" itself - that would flash idle for a frame before
    continuous mode's status immediately overwrote it."""
    from jarvis_engine.voice.tts_engine import tts_engine
    from jarvis_engine.voice.voice_manager import voice_manager

    try:
        clean = clean_text_for_tts(response_text)
        if clean and len(clean) > 3:
            tts_engine.speak_sync(
                clean, on_speech_start=lambda: _post_status("speaking")
            )
    except Exception as e:
        print(f"TTS error: {e}")
    finally:
        voice_manager.continue_conversation()


def handle_transcription(
    text: str, direct_result: str = None, conversation_id: str = None
):
    """Entry point invoked by VoiceManager once speech is transcribed."""
    print(f"[VOICE COMMAND] {text}")

    # Direct command already executed - just broadcast and speak
    if direct_result:
        print(f"[VOICE DIRECT] {direct_result}")

        def speak_and_broadcast():
            import requests

            # Broadcast to UI first
            try:
                payload = {"text": text, "direct_response": direct_result}
                if conversation_id:
                    payload["conversation_id"] = conversation_id
                requests.post(VOICE_INPUT_URL, json=payload, timeout=10)
            except Exception as e:
                print(f"Broadcast error: {e}")

            _speak_response(direct_result)

        threading.Thread(target=speak_and_broadcast, daemon=True).start()
        return

    # LLM pipeline - POST the text, then speak whatever comes back
    def send_and_speak():
        import requests

        try:
            payload = {"text": text}
            if conversation_id:
                payload["conversation_id"] = conversation_id
            response = requests.post(VOICE_INPUT_URL, json=payload, timeout=60)
            if response.status_code == 200:
                ai_response = response.json().get("response", "")
                if ai_response:
                    safe_print(f"[JARVIS SPEAKING] {ai_response}")
                    _speak_response(ai_response)
                else:
                    _post_status("idle")
            else:
                _post_status("idle")
        except Exception as e:
            print(f"[VOICE ERROR] {e}")
            _post_status("idle")

    threading.Thread(target=send_and_speak, daemon=True).start()
