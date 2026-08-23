import numpy as np
import threading
import tempfile
import os
import subprocess
import time
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
    import ctypes
    vk_map = {
      "up": 0xAF,     # VK_VOLUME_UP
      "down": 0xAE,   # VK_VOLUME_DOWN
      "mute": 0xAD,   # VK_VOLUME_MUTE
    }
    if param in vk_map:
      vk = vk_map[param]
      ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
      ctypes.windll.user32.keybd_event(vk, 0, 2, 0)  # KEYEVENTF_KEYUP
    return f"Volume {param}, sir."

  elif action == "system_query":
    if param == "time":
      from datetime import datetime
      now = datetime.now().strftime("%I:%M %p")
      return f"The time is {now}, sir."
    elif param == "ip":
      import socket
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
      except Exception:
        ip = socket.gethostbyname(socket.gethostname())
      return f"Your IP is {ip}, sir."
    elif param == "battery":
      import ctypes
      class SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [
          ("ACLineStatus", ctypes.c_byte),
          ("BatteryFlag", ctypes.c_byte),
          ("BatteryLifePercent", ctypes.c_byte),
          ("SystemStatusFlag", ctypes.c_byte),
          ("BatteryLifeTime", ctypes.c_ulong),
          ("BatteryFullLifeTime", ctypes.c_ulong),
        ]
      status = SYSTEM_POWER_STATUS()
      if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        if status.BatteryLifePercent != 255:
          charging = "charging" if status.ACLineStatus == 1 else "on battery"
          return f"Battery is at {status.BatteryLifePercent}% ({charging}), sir."
        else:
          return "System is running on AC power with no battery, sir."
      return "Unable to retrieve battery status, sir."

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
    self.whisper_ready = threading.Event()
    self.wake_word_ready = threading.Event()
    self._initialized = False

  def _set_is_listening(self, val: bool):
    self.is_listening = val

  def initialize(
    self,
    on_transcription: callable
  ):
    """Kicks off Whisper and wake-word loading in background daemon
    threads and returns immediately - it does NOT block on either model
    being ready. Check self.whisper_ready / self.wake_word_ready (or
    GET /health's voice_ready field) for real readiness.

    Safe to call more than once (e.g. startup, then POST /voice/start):
    the handler is refreshed but the models/mic stream are only brought up
    once. Re-running the loaders would open a SECOND InputStream and
    dispatch every wake word twice."""
    self.on_transcription = on_transcription

    if self._initialized:
      print("Voice manager already initialized - refreshed handler only")
      return
    self._initialized = True

    def _load_whisper():
      _t_whisper = time.time()
      try:
        from faster_whisper import WhisperModel
        print("Loading Whisper model in background...")
        self.whisper_model = WhisperModel(
          "small.en",
          device="cpu",
          compute_type="int8"
        )
        print(f"Whisper model ready! [{time.time() - _t_whisper:.2f}s]")
      except Exception as e:
        print(f"Whisper load failed: {e} [{time.time() - _t_whisper:.2f}s]")
        self.whisper_model = None
      finally:
        self.whisper_ready.set()

    def _load_wake_word():
      _t_wake = time.time()
      self.wake_word_detector = WakeWordDetector(
        model_path=self.model_path,
        on_detected=self._on_wake_word_detected,
        # threshold / barge-in tuning come from core/config.py defaults.
        threshold=settings.WAKE_WORD_THRESHOLD,
        get_is_listening=lambda: self.is_listening,
        set_is_listening=self._set_is_listening,
        cooldown_seconds=2.0,
        tts_mute_buffer_seconds=settings.WAKE_WORD_TTS_MUTE_BUFFER_SECONDS
      )
      print(f"[TIMING] WakeWordDetector construction (openWakeWord Model load): {time.time() - _t_wake:.2f}s")
      _t_wake_start = time.time()
      self.wake_word_detector.start()
      print(f"[TIMING] WakeWordDetector.start() (mic stream open): {time.time() - _t_wake_start:.2f}s")
      self.wake_word_ready.set()

    threading.Thread(target=_load_whisper, daemon=True, name="whisper-loader").start()
    threading.Thread(target=_load_wake_word, daemon=True, name="wakeword-loader").start()
    print("Voice manager initialize() returned - Whisper + wake word loading in background")
  
  def _on_wake_word_detected(self):
    try:
      self.is_listening = True

      # Respond immediately
      print("[VOICE] Wake word detected - responding")

      # Broadcast listening status immediately
      import requests
      try:
        requests.post(
          "http://localhost:8765/voice/status/update",
          json={"status": "listening"},
          timeout=2
        )
      except Exception:
        pass

      from .tts_engine import tts_engine

      def say_yes():
        tts_engine.speak_sync("Yes sir?")

      t = threading.Thread(target=say_yes, daemon=True)
      t.start()
      t.join(timeout=3)  # Wait for "Yes sir?" to finish before recording

      print("[VOICE] Recording command...")

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
              else:
                print("[VOICE] Recorded audio but transcription was empty.")

                def _broadcast_speaking():
                  try:
                    requests.post(
                      "http://localhost:8765/voice/status/update",
                      json={"status": "speaking"},
                      timeout=2
                    )
                  except Exception:
                    pass

                tts_engine.speak_sync(
                  "Didn't catch that, sir.",
                  on_speech_start=_broadcast_speaking
                )
                try:
                  requests.post(
                    "http://localhost:8765/voice/status/update",
                    json={"status": "idle"},
                    timeout=2
                  )
                except Exception:
                  pass
            else:
              print("[VOICE] No speech detected within timeout.")
              try:
                requests.post(
                  "http://localhost:8765/voice/status/update",
                  json={"status": "idle"},
                  timeout=2
                )
              except Exception:
                pass
          except Exception as e:
            print(f"Voice processing error: {e}")
            try:
              requests.post(
                "http://localhost:8765/voice/status/update",
                json={"status": "idle"},
                timeout=2
              )
            except Exception:
              pass
          finally:
            self.is_listening = False

      t2 = threading.Thread(target=process_voice, daemon=True)
      t2.start()
    except Exception as e:
      print(f"[VOICE] Wake word handling error: {e}")
      try:
        requests.post(
          "http://localhost:8765/voice/status/update",
          json={"status": "idle"},
          timeout=2
        )
      except Exception:
        pass
      self.is_listening = False
  
  def _transcribe(
    self, audio: np.ndarray
  ) -> str:
    if not self.whisper_ready.is_set():
      print("Whisper still warming up, waiting...")
      self.whisper_ready.wait(timeout=30)
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
    # Allow a later initialize() to bring the models back up.
    self._initialized = False
    self.whisper_ready.clear()
    self.wake_word_ready.clear()

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
