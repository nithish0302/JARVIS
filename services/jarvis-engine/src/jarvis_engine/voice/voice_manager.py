import numpy as np
import threading
import tempfile
import os
import subprocess
from pathlib import Path
from .wake_word import WakeWordDetector
from .speech_recorder import SpeechRecorder
from ..core.config import settings

# Whitelisted applications for voice commands (SECURITY: prevents command injection)
ALLOWED_APPS = {
  "notepad.exe", "calc.exe", "firefox", "chrome", "explorer.exe",
  "code", "spotify", "discord", "taskmgr.exe",
  "ms-settings:", "ms-windows-store:"
}

# Direct command mapping for instant execution without LLM
VOICE_COMMAND_MAP = {
  "open notepad": ("open_app", "notepad.exe"),
  "open calculator": ("open_app", "calc.exe"),
  "open calc": ("open_app", "calc.exe"),
  "open firefox": ("open_app", "firefox"),
  "open chrome": ("open_app", "chrome"),
  "open explorer": ("open_app", "explorer.exe"),
  "open file explorer": ("open_app", "explorer.exe"),
  "open vs code": ("open_app", "code"),
  "open vscode": ("open_app", "code"),
  "open spotify": ("open_app", "spotify"),
  "open discord": ("open_app", "discord"),
  "open task manager": ("open_app", "taskmgr.exe"),
  "lock screen": ("lock_screen", None),
  "lock my screen": ("lock_screen", None),
  "lock the screen": ("lock_screen", None),
  "volume up": ("volume", "up"),
  "volume down": ("volume", "down"),
  "mute": ("volume", "mute"),
  "unmute": ("volume", "unmute"),
  "take screenshot": ("screenshot", None),
  "open settings": ("open_app", "ms-settings:"),
  "open store": ("open_app", "ms-windows-store:"),
  "what time is it": ("system_query", "time"),
  "what is the time": ("system_query", "time"),
  "what is my ip": ("system_query", "ip"),
  "my ip address": ("system_query", "ip"),
  "battery level": ("system_query", "battery"),
  "battery status": ("system_query", "battery"),
}

def execute_voice_command(text: str) -> str | None:
  """Try to execute a direct voice command. Returns response if handled, None if not."""
  msg = text.lower().strip().rstrip(".,!?")

  # Exact match
  if msg in VOICE_COMMAND_MAP:
    action, param = VOICE_COMMAND_MAP[msg]
    return _execute_action(action, param)

  # Partial match
  for cmd, (action, param) in VOICE_COMMAND_MAP.items():
    if cmd in msg:
      return _execute_action(action, param)

  return None  # Not a direct command

def _execute_action(action: str, param: str | None) -> str:
  """Execute a direct voice action and return response."""
  if action == "open_app":
    # SECURITY: Whitelist validation to prevent command injection
    if param not in ALLOWED_APPS:
      print(f"[SECURITY] Blocked attempt to open non-whitelisted app: {param}")
      return f"Application '{param}' is not whitelisted for voice commands, sir."

    try:
      subprocess.Popen(
        ["cmd", "/C", "start", "", param],
        creationflags=subprocess.CREATE_NO_WINDOW
      )
      app_name = param.replace(".exe","").replace("ms-","").replace(":","").title()
      return f"Opening {app_name}, sir."
    except Exception as e:
      return f"Failed to open: {e}"

  elif action == "lock_screen":
    subprocess.Popen(
      ["rundll32.exe","user32.dll,LockWorkStation"]
    )
    return "Screen locked, sir."

  elif action == "volume":
    scripts = {
      "up": "(New-Object -comObject WScript.Shell).SendKeys([char]175)",
      "down": "(New-Object -comObject WScript.Shell).SendKeys([char]174)",
      "mute": "(New-Object -comObject WScript.Shell).SendKeys([char]173)",
    }
    if param in scripts:
      subprocess.Popen(
        ["powershell","-Command",scripts[param]],
        creationflags=subprocess.CREATE_NO_WINDOW
      )
    return f"Volume {param}, sir."

  elif action == "system_query":
    if param == "time":
      from datetime import datetime
      now = datetime.now().strftime("%I:%M %p")
      return f"The time is {now}, sir."
    elif param == "ip":
      import socket
      ip = socket.gethostbyname(socket.gethostname())
      return f"Your IP is {ip}, sir."
    elif param == "battery":
      result = subprocess.run(
        ["powershell","-Command",
         "Get-WmiObject Win32_Battery | Select-Object EstimatedChargeRemaining | ConvertTo-Json"],
        capture_output=True, text=True
      )
      return f"Checking battery... {result.stdout[:50]}"

  return "Done, sir."

class VoiceManager:
  def __init__(self):
    self.is_listening = False
    self.wake_word_detector = None
    self.speech_recorder = SpeechRecorder()
    self.on_transcription = None

    # Get the jarvis-engine root directory
    # voice_manager.py is at: jarvis-engine/src/jarvis_engine/voice/voice_manager.py
    # So we need to go up 4 levels to reach jarvis-engine/
    engine_root = Path(__file__).parent.parent.parent.parent
    self.model_path = str(engine_root / "models" / "wake_up_jarvis.onnx")
    print(f"Looking for wake word model at: {self.model_path}")
    self.whisper_model = None
  
  def initialize(
    self,
    on_transcription: callable
  ):
    self.on_transcription = on_transcription

    # Load Whisper model first (before wake word)
    try:
      from faster_whisper import WhisperModel
      print("Loading Whisper model at startup...")
      self.whisper_model = WhisperModel(
        "small.en",
        device="cpu",
        compute_type="int8"
      )
      print("Whisper model ready!")
    except Exception as e:
      print(f"Whisper load failed: {e}")
      self.whisper_model = None

    # Then start wake word detection
    self.wake_word_detector = WakeWordDetector(
      model_path=self.model_path,
      on_detected=self._on_wake_word_detected,
      threshold=0.3,
      get_is_listening=lambda: self.is_listening
    )
    self.wake_word_detector.start()
    print("Voice manager initialized")
  
  def _on_wake_word_detected(self):
    if self.is_listening:
      return
    self.is_listening = True

    # Respond immediately
    print("[VOICE] Wake word detected - responding")
    from .tts_engine import tts_engine

    def say_yes():
      tts_engine.speak_sync("Yes sir?")

    t = threading.Thread(target=say_yes, daemon=True)
    t.start()
    t.join(timeout=3)  # Wait max 3 seconds

    print("[VOICE] Recording command...")

    # Broadcast listening status
    import requests
    try:
      requests.post(
        "http://localhost:8765/voice/status/update",
        json={"status": "listening"},
        timeout=2
      )
    except:
      pass

    def process_voice():
        try:
          # Record speech
          audio = self.speech_recorder.record()

          if len(audio) > 0:
            # Transcribe with faster-whisper
            text = self._transcribe(audio)
            if text and text.strip():
              # Try direct command first
              direct_result = execute_voice_command(text.strip())
              if direct_result:
                print(f"[VOICE DIRECT] {direct_result}")
                if self.on_transcription:
                  self.on_transcription(text.strip(), direct_result)
              else:
                # No direct command match - use LLM
                if self.on_transcription:
                  self.on_transcription(text.strip(), None)
        except Exception as e:
          print(f"Voice processing error: {e}")
        finally:
          self.is_listening = False
          # Broadcast idle status
          import requests
          try:
            requests.post(
              "http://localhost:8765/voice/status/update",
              json={"status": "idle"},
              timeout=2
            )
          except:
            pass

    t2 = threading.Thread(target=process_voice, daemon=True)
    t2.start()
  
  def _transcribe(
    self, audio: np.ndarray
  ) -> str:
    if not self.whisper_model:
      print("Whisper not loaded")
      return ""
    try:
      # Use self.whisper_model directly
      # No loading here - model already loaded
      import soundfile as sf

      audio_16 = (audio * 32768).astype(np.int16)
      with tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False
      ) as tmp:
        sf.write(tmp.name, audio_16, 16000,
                 subtype="PCM_16")
        tmp_path = tmp.name

      segments, _ = self.whisper_model.transcribe(
        tmp_path,
        language="en",
        task="transcribe"
      )
      text = " ".join(
        seg.text for seg in segments
      ).strip()
      os.unlink(tmp_path)
      # Removed duplicate print - already printed in process_voice
      return text
    except Exception as e:
      print(f"Transcription error: {e}")
      return ""
  
  def shutdown(self):
    """Clean up resources on shutdown."""
    if self.wake_word_detector:
      self.wake_word_detector.stop()
      self.wake_word_detector = None

    # Clean up Whisper model to free memory (~140MB)
    if self.whisper_model:
      print("Cleaning up Whisper model...")
      del self.whisper_model
      self.whisper_model = None

      # Force garbage collection to free memory immediately
      import gc
      gc.collect()
      print("Voice manager shutdown complete")

voice_manager = VoiceManager()
