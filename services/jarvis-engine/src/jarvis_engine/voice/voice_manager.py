import numpy as np
import re
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

def _register_cuda_dll_dirs():
  """faster-whisper's CTranslate2 backend links against cuBLAS/cuDNN by a
  CUDA-12-specific filename (cublas64_12.dll, cudnn64_9.dll) regardless of
  the driver's own CUDA version. Without this, WhisperModel(device="cuda")
  *constructs* successfully but fails the moment it actually runs inference
  ("cublas64_12.dll is not found").

  os.add_dll_directory() does NOT fix this - CTranslate2's native extension
  loads these libraries in a way that only honors PATH, not the
  AddDllDirectory-registered search list. Prepending to PATH is the only
  approach verified to work here.

  cuBLAS comes from the nvidia-cublas-cu12 pip package (cublas64_12.dll -
  no naming collision with torch's own cublas64_13.dll). cuDNN deliberately
  does NOT come from a separate nvidia-cudnn-cu12 package: that DLL is
  named cudnn64_9.dll in EVERY nvidia-cudnn-cu* package regardless of CUDA
  major version, identical to the name torch already bundles under
  torch/lib. Installing a second, differently-built copy causes Kokoro's
  torch CUDA calls to intermix DLLs from both installs mid-process
  ("CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH"). Pointing CTranslate2 at
  torch's own torch/lib instead gives both consumers the same, internally
  consistent cuDNN build."""
  if os.name != "nt":
    return
  try:
    import importlib.util
    dirs = []
    spec = importlib.util.find_spec("nvidia.cublas")
    if spec and spec.submodule_search_locations:
      for loc in spec.submodule_search_locations:
        bin_dir = os.path.join(loc, "bin")
        if os.path.isdir(bin_dir):
          dirs.append(bin_dir)

    torch_spec = importlib.util.find_spec("torch")
    if torch_spec and torch_spec.submodule_search_locations:
      for loc in torch_spec.submodule_search_locations:
        lib_dir = os.path.join(loc, "lib")
        if os.path.isdir(lib_dir):
          dirs.append(lib_dir)

    if dirs:
      os.environ["PATH"] = os.pathsep.join(dirs) + os.pathsep + os.environ.get("PATH", "")
  except Exception as e:
    print(f"[VOICE] Failed to register CUDA DLL directories: {e}")


def _matches_interrupt_phrase(normalized_text: str, phrase: str) -> bool:
  """True if normalized_text (already lowercased/stripped) IS phrase, or
  starts with phrase followed by a word boundary - so "stop please" and
  the doubled "wake up jarvis wake up jarvis" from the original bug
  report both match, but "stopwatch" or "waiting" don't."""
  if normalized_text == phrase:
    return True
  return re.match(re.escape(phrase) + r"\b", normalized_text) is not None


def match_interrupt_phrase(text: str) -> str | None:
  """Checks a FINAL Whisper transcript against settings.WAKE_PHRASE and
  settings.INTERRUPT_PHRASES (see core/config.py for the full rationale).
  Returns "wake" if it's the wake phrase, "stop" if it's one of the other
  interrupt phrases, None if it's an ordinary command."""
  normalized = text.lower().strip().rstrip(".,!?")
  if _matches_interrupt_phrase(normalized, settings.WAKE_PHRASE.lower()):
    return "wake"
  for phrase in settings.INTERRUPT_PHRASES:
    if _matches_interrupt_phrase(normalized, phrase.lower()):
      return "stop"
  return None


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
      if settings.USE_GPU:
        _register_cuda_dll_dirs()
      from faster_whisper import WhisperModel
      print("Loading Whisper model in background...")

      # GPU path: try float16 first, then int8 on the same device (some
      # cards/driver combos choke on fp16 kernels), then fall back to CPU
      # entirely if CUDA init fails. Log which path actually loaded so it's
      # diagnosable in the field, not just at implementation time.
      attempts = []
      if settings.USE_GPU:
        attempts.append(("cuda", "float16"))
        attempts.append(("cuda", "int8_float16"))
      attempts.append(("cpu", "int8"))

      for device, compute_type in attempts:
        try:
          model = WhisperModel(
            "small.en",
            device=device,
            compute_type=compute_type
          )
          # Construction alone doesn't prove the device works - CTranslate2
          # loads cuBLAS/cuDNN lazily, so a missing DLL or incompatible
          # kernel only surfaces on the first real inference. Run one to
          # actually validate this attempt before committing to it.
          list(model.transcribe(
            np.zeros(16000, dtype=np.float32), language="en"
          )[0])
          self.whisper_model = model
          print(
            f"Whisper model ready! device={device} "
            f"compute_type={compute_type} [{time.time() - _t_whisper:.2f}s]"
          )
          break
        except Exception as e:
          print(f"Whisper load failed on device={device} compute_type={compute_type}: {e}")
          self.whisper_model = None
      else:
        print(f"Whisper load failed on all devices [{time.time() - _t_whisper:.2f}s]")

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
      self._start_listening_cycle()
    except Exception as e:
      print(f"[VOICE] Wake word handling error: {e}")
      self._broadcast_status("idle")
      self.is_listening = False

  def _broadcast_status(self, status: str):
    import requests
    try:
      requests.post(
        "http://localhost:8765/voice/status/update",
        json={"status": status},
        timeout=2
      )
    except Exception:
      pass

  def _start_listening_cycle(self):
    """Says "Yes sir?" and opens a new recording window in parallel - the
    normal wake-word trigger path, but also reused by the wake-phrase
    interrupt below (match_interrupt_phrase() returning "wake") so hearing
    the wake phrase mid-response reaches the exact same fresh cycle the
    wake-word MODEL would give if it weren't muted during TTS."""
    self.is_listening = True

    # Respond immediately
    print("[VOICE] Wake word detected - responding")
    self._broadcast_status("listening")

    from .tts_engine import tts_engine

    # Set the instant "Yes sir?" playback genuinely finishes (is_speaking
    # True -> False), not when this thread happens to be joined or timed
    # out. The recording thread below starts immediately in parallel - it
    # does NOT wait on this event before opening the mic, only before
    # starting its own wait_for_speech_timeout countdown (see
    # SpeechRecorder.record).
    tts_finished_event = threading.Event()

    def say_yes():
      tts_engine.speak_sync(
        "Yes sir?",
        on_speech_end=tts_finished_event.set
      )

    t = threading.Thread(target=say_yes, daemon=True)
    t.start()

    print("[VOICE] Recording command...")
    t2 = threading.Thread(
      target=self._process_voice_command, args=(tts_finished_event,), daemon=True
    )
    t2.start()

  def _process_voice_command(self, tts_finished_event: threading.Event):
    # Set (not reset to False in the finally below) only when this
    # recording resolves to the wake-phrase interrupt, which re-arms a
    # fresh cycle via _start_listening_cycle() - that call already sets
    # is_listening back to True, and letting the finally below clobber it
    # to False immediately after would create a race where the new cycle
    # looks "not listening" until its own recording thread gets going.
    rearmed = False
    try:
      # Record speech - mic opens immediately, in parallel with "Yes sir?"
      # still playing; only the no-speech timeout waits on tts_finished_event.
      audio = self.speech_recorder.record(tts_finished_event=tts_finished_event)

      if len(audio) > 0:
        # Transcribe with faster-whisper
        text = self._transcribe(audio)
        if text and text.strip():
          clean_text = text.strip()

          # PHRASE-BASED INTERRUPT CHECK - on the FINAL transcript only,
          # before this text goes anywhere near execute_voice_command or
          # the LLM. Complements (doesn't replace) the loudness-based
          # barge-in in wake_word.py: that one reacts to volume alone and
          # doesn't know what was said; this one recognizes specific
          # phrases regardless of volume and decides what happens next.
          interrupt = match_interrupt_phrase(clean_text)
          if interrupt:
            print(f"[VOICE] Interrupt phrase detected ({interrupt}): {clean_text!r}")
            from .tts_engine import tts_engine
            if tts_engine.is_speaking:
              tts_engine.stop()
            if interrupt == "wake":
              # Fresh cycle: new "Yes sir?" + new recording window, same
              # as a normal wake-word trigger.
              rearmed = True
              self._start_listening_cycle()
            else:
              # "stop"/"wait"/"cancel"/etc - just stop, no new
              # acknowledgment, back to idle/listening.
              self._broadcast_status("idle")
            return

          # Try direct command first
          direct_result = execute_voice_command(clean_text)
          if direct_result:
            print(f"[VOICE DIRECT] {direct_result}")
            if self.on_transcription:
              self.on_transcription(clean_text, direct_result)
          else:
            # No direct command match - use LLM
            if self.on_transcription:
              self.on_transcription(clean_text, None)
        else:
          print("[VOICE] Recorded audio but transcription was empty.")

          from .tts_engine import tts_engine
          tts_engine.speak_sync(
            "Didn't catch that, sir.",
            on_speech_start=lambda: self._broadcast_status("speaking")
          )
          self._broadcast_status("idle")
      else:
        print("[VOICE] No speech detected within timeout.")
        self._broadcast_status("idle")
    except Exception as e:
      print(f"Voice processing error: {e}")
      self._broadcast_status("idle")
    finally:
      if not rearmed:
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
