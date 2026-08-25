import asyncio
import os
import queue
import re
import tempfile
import threading
import time
import traceback
from typing import Optional
import numpy as np


# --- Diagnostic instrumentation (Phase 6 TTS latency investigation) -------
# Reports where wall-clock time actually goes inside a synthesis call, and
# whether the process is faulting pages back in from disk while it happens.
# Pure measurement: nothing here changes synthesis behaviour.

def _mem_probe() -> dict:
  """System RAM load + this process's cumulative hard/soft page-fault count.
  A large PageFaultCount delta across a slow call means the process is
  being served from the pagefile rather than RAM."""
  out = {"ram_pct": -1, "avail_mb": -1, "faults": -1, "ws_mb": -1}
  try:
    import ctypes

    class _MEMSTATUS(ctypes.Structure):
      _fields_ = [
        ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
      ]

    st = _MEMSTATUS()
    st.dwLength = ctypes.sizeof(_MEMSTATUS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    out["ram_pct"] = st.dwMemoryLoad
    out["avail_mb"] = int(st.ullAvailPhys / (1024 * 1024))

    class _PMC(ctypes.Structure):
      _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
      ]

    from ctypes import wintypes

    pmc = _PMC()
    pmc.cb = ctypes.sizeof(_PMC)
    k32 = ctypes.windll.kernel32
    # GetCurrentProcess returns the pseudo-handle (HANDLE)-1; without an
    # explicit restype/argtypes ctypes tries to marshal it as a C int and
    # raises "int too long to convert".
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    # K32GetProcessMemoryInfo (kernel32) is the modern export; the older
    # psapi.dll name isn't always resolvable, so try both.
    fn = getattr(k32, "K32GetProcessMemoryInfo", None)
    if fn is None:
      fn = ctypes.windll.psapi.GetProcessMemoryInfo
    fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PMC), ctypes.c_ulong]
    fn.restype = wintypes.BOOL
    if fn(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
      out["faults"] = pmc.PageFaultCount
      out["ws_mb"] = int(pmc.WorkingSetSize / (1024 * 1024))
  except Exception:
    pass
  return out


class TTSEngine:
  def __init__(self):
    self._is_speaking = False
    # Wall-clock time at which speech last STOPPED. The wake-word
    # detector gates on this (plus a config buffer) so that JARVIS's own
    # audio - including the room echo / speaker decay tail - is never fed
    # into the wake-word model. Maintained by the is_speaking setter, so
    # every site that clears the flag updates it automatically.
    self.last_speech_end_time = 0.0
    # Wall-clock time at which audio playback last STARTED. Distinct from
    # speak_start_time below, which is stamped when speak() is *called* -
    # potentially seconds earlier, since speak() may block on the Kokoro
    # warmup and on time-to-first-audio. The barge-in grace period must be
    # measured from real playback start, otherwise TTFB latency eats the
    # whole window and JARVIS's own voice trips the interrupt immediately.
    # Maintained by the is_speaking setter, so every site that sets the
    # flag updates it automatically.
    self.last_speech_start_time = 0.0
    self.stop_requested = False
    self.speak_start_time = 0.0
    self.current_tmp_path = None
    # Callback invoked the moment is_speaking flips False -> True, i.e. the
    # instant audio actually starts playing. speak_sync()'s on_speech_start
    # param sets this so callers (e.g. status broadcasts) can react to real
    # playback start instead of the speak_sync() call itself, which can
    # precede audible audio by seconds (Kokoro TTFB).
    self._on_speech_start = None
    # Callback invoked the moment is_speaking flips True -> False, i.e. the
    # instant playback genuinely finishes. speak_sync()'s on_speech_end
    # param sets this so callers (e.g. the post-wake-word recording window)
    # can anchor a timeout to real playback completion instead of to
    # whenever they happened to call speak_sync() or join() a synthesis
    # thread with a fixed timeout - which drifts on a slow synthesis call.
    self._on_speech_end = None
    # DIAGNOSTIC: synthesis sequence counter + in-flight flag, used to
    # detect whether two speak_sync() calls overlap on the shared engine
    # state (audio_queue / stop_event / persistent OutputStream).
    self._synth_seq = 0
    self._synth_active = False
    self._synth_active_seq = 0
    self._diag_seq_current = 0

    self.audio_queue = queue.Queue()
    self.current_chunk: Optional[np.ndarray] = None
    self.chunk_offset = 0
    self.stop_event = threading.Event()
    self.stream = None

    # Persistent sounddevice OutputStream
    _t_sd = time.time()
    try:
      import sounddevice as sd

      def _audio_callback(outdata, frames, time_info, status):
        if self.stop_event.is_set():
          outdata.fill(0)
          return

        filled = 0
        while filled < frames:
          if self.current_chunk is None or self.chunk_offset >= len(self.current_chunk):
            try:
              self.current_chunk = self.audio_queue.get_nowait()
              self.chunk_offset = 0
            except queue.Empty:
              self.current_chunk = None
              self.chunk_offset = 0
              outdata[filled:].fill(0)
              break

          needed = frames - filled
          avail = len(self.current_chunk) - self.chunk_offset
          take = min(needed, avail)
          chunk_slice = self.current_chunk[self.chunk_offset : self.chunk_offset + take]
          if chunk_slice.ndim == 1:
            outdata[filled : filled + take, 0] = chunk_slice
          else:
            outdata[filled : filled + take] = chunk_slice
          self.chunk_offset += take
          filled += take

      self.stream = sd.OutputStream(
        samplerate=24000,
        channels=1,
        dtype='float32',
        callback=_audio_callback
      )
      self.stream.start()
      print(f"[TTS] Persistent sounddevice stream ready (24000Hz, mono, float32) [{time.time() - _t_sd:.2f}s]")
    except Exception as e:
      self.stream = None
      print(f"[TTS] sounddevice OutputStream init error: {e} [{time.time() - _t_sd:.2f}s]")

    # Primary TTS Engine: Kokoro
    # NOTE: KPipeline construction (~6-14s, mostly disk + model weight
    # load) is NOT done here synchronously. It's kicked off in a daemon
    # thread below and tracked via self.kokoro_ready, so constructing a
    # TTSEngine (which happens at module import time) returns almost
    # instantly. speak_sync() waits on kokoro_ready if called before the
    # background load finishes, instead of blocking startup or crashing.
    self.kokoro_pipeline = None
    self.kokoro_voice = "am_michael"
    self.kokoro_ready = threading.Event()
    try:
      from jarvis_engine.core.config import settings
      self.kokoro_voice = getattr(settings, "TTS_KOKORO_VOICE", "am_michael")
    except Exception:
      pass

    def _load_kokoro():
      _t_kokoro = time.time()
      try:
        from kokoro import KPipeline
        print(f"[TIMING] kokoro import: {time.time() - _t_kokoro:.2f}s")

        device = "cpu"
        try:
          from jarvis_engine.core.config import settings as _settings
          if getattr(_settings, "USE_GPU", True):
            import torch
            if torch.cuda.is_available():
              device = "cuda"
        except Exception as e:
          print(f"[TTS] GPU check failed, using CPU: {e}")

        _t_kpipeline = time.time()
        try:
          self.kokoro_pipeline = KPipeline(lang_code='a', device=device)
        except Exception as e:
          if device == "cuda":
            print(f"[TTS] Kokoro CUDA init failed ({e}), retrying on CPU")
            device = "cpu"
            self.kokoro_pipeline = KPipeline(lang_code='a', device=device)
          else:
            raise
        print(f"[TIMING] KPipeline(lang_code='a', device={device!r}) construction: {time.time() - _t_kpipeline:.2f}s")
        print(f"[TTS] Kokoro TTS ready (voice: {self.kokoro_voice}) [total {time.time() - _t_kokoro:.2f}s]")
        self.kokoro_ready.set()

        # Warmup model, still in this same background thread
        try:
          _t_warm = time.time()
          for _ in self.kokoro_pipeline("ready", voice=self.kokoro_voice, speed=1.0):
            pass
          print(f"[TIMING] Kokoro background warmup: {time.time() - _t_warm:.2f}s")
        except Exception:
          pass
      except (ImportError, RuntimeError, Exception) as e:
        self.kokoro_pipeline = None
        print(f"[TTS] Kokoro TTS init failed: {e}. Falling back to edge-tts. [{time.time() - _t_kokoro:.2f}s]")
        traceback.print_exc()
        self.kokoro_ready.set()

    threading.Thread(target=_load_kokoro, daemon=True, name="kokoro-loader").start()
    print("[TTS] Kokoro loading in background thread (not blocking startup)")

    print("[TTS] Andrew Multilingual voice ready (fallback)")

  @property
  def is_speaking(self) -> bool:
    return self._is_speaking

  @is_speaking.setter
  def is_speaking(self, value: bool):
    value = bool(value)
    # Record the moment speech stops so the wake-word mute window can
    # extend past it by the configured buffer.
    if self._is_speaking and not value:
      self.last_speech_end_time = time.time()
      if self._on_speech_end is not None:
        try:
          self._on_speech_end()
        except Exception:
          pass
    # Record the moment playback actually starts so the barge-in grace
    # period is measured from audible speech, not from the speak() call.
    if value and not self._is_speaking:
      self.last_speech_start_time = time.time()
      if self._on_speech_start is not None:
        try:
          self._on_speech_start()
        except Exception:
          pass
    self._is_speaking = value

  def _clean_text(self, text: str) -> str:
    text = re.sub(r'\[UI_ACTION:[^\]]*\]', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'http\S+', '', text)
    text = ' '.join(text.split())
    return text.strip()

  def _speak_sync_kokoro(self, clean: str) -> bool:
    try:
      gen_error = None
      first_chunk_logged = False
      generation_finished = threading.Event()
      seq = self._diag_seq_current
      t_gen_enter = time.time()
      diag = {"t_pipeline_call": None, "t_first_chunk": None, "chunks": 0}

      def generator_thread():
        nonlocal gen_error, first_chunk_logged
        try:
          # Time the KPipeline __call__ itself (model setup / graph build)
          # separately from iterating it (actual inference per chunk).
          t0 = time.time()
          gen = self.kokoro_pipeline(clean, voice=self.kokoro_voice, speed=1.0)
          diag["t_pipeline_call"] = time.time() - t0
          for result in gen:
            if self.stop_requested or self.stop_event.is_set():
              break

            audio = result.audio
            if hasattr(audio, 'numpy'):
              audio_arr = audio.numpy()
            elif isinstance(audio, np.ndarray):
              audio_arr = audio
            else:
              audio_arr = np.array(audio, dtype=np.float32)

            if audio_arr.dtype != np.float32:
              audio_arr = audio_arr.astype(np.float32)

            if not first_chunk_logged:
              self.is_speaking = True
              first_chunk_logged = True
              ttfb = (time.time() - self.speak_start_time) * 1000
              diag["t_first_chunk"] = time.time() - t_gen_enter
              print(f"[TTS][Kokoro] Time to first audio: {ttfb:.1f}ms")
              print(
                f"[TTS][DIAG#{seq}] generation: "
                f"pipeline_call={1000*(diag['t_pipeline_call'] or 0):.1f}ms "
                f"first_chunk_inference={1000*diag['t_first_chunk']:.1f}ms"
              )

            diag["chunks"] += 1
            t_q = time.time()
            self.audio_queue.put(audio_arr)
            q_ms = 1000 * (time.time() - t_q)
            if q_ms > 5:
              print(f"[TTS][DIAG#{seq}] slow queue.put: {q_ms:.1f}ms")
        except Exception as e:
          gen_error = e
        finally:
          generation_finished.set()

      t = threading.Thread(target=generator_thread, daemon=True)
      t.start()

      while not self.stop_requested and not self.stop_event.is_set():
        if generation_finished.is_set():
          if gen_error:
            if not first_chunk_logged:
              return False
            print(f"[TTS][Kokoro] Generation error: {gen_error}")
            break
          if self.audio_queue.empty() and self.current_chunk is None:
            break
        time.sleep(0.01)

      if not self.stop_requested and not self.stop_event.is_set() and not gen_error:
        print("[TTS] Playback complete")
        print(
          f"[TTS][DIAG#{seq}] drain: gen+playback={1000*(time.time()-t_gen_enter):.1f}ms "
          f"chunks={diag['chunks']}"
        )
      return True if first_chunk_logged or not gen_error else False
    except Exception as e:
      print(f"[TTS] Kokoro execution error: {e}")
      return False
    finally:
      self.is_speaking = False

  async def _stream_and_play_edge_tts(self, text: str):
    try:
      import edge_tts
      import pygame
      from jarvis_engine.core.config import settings

      voice = getattr(
        settings, 'EDGE_TTS_VOICE',
        'en-US-AndrewMultilingualNeural'
      )
      rate = getattr(
        settings, 'EDGE_TTS_RATE', '+5%'
      )

      communicate = edge_tts.Communicate(
        text=text, voice=voice, rate=rate
      )

      audio_data = b""
      async for chunk in communicate.stream():
        if self.stop_requested:
          return
        if chunk["type"] == "audio":
          audio_data += chunk["data"]

      if not audio_data or self.stop_requested:
        return

      tmp = tempfile.NamedTemporaryFile(
        suffix='.mp3', delete=False
      )
      tmp.write(audio_data)
      tmp.close()
      tmp_path = tmp.name
      self.current_tmp_path = tmp_path

      try:
        if not pygame.mixer.get_init():
          pygame.mixer.init(frequency=44100)
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
          if self.stop_requested:
            pygame.mixer.music.stop()
            break
          time.sleep(0.05)
      finally:
        try:
          time.sleep(0.3)
          os.unlink(tmp_path)
          self.current_tmp_path = None
        except Exception:
          pass

    except Exception as e:
      print(f"[TTS] Edge-TTS stream error: {e}")

  def _speak_sync_edge_tts(self, clean: str):
    self.is_speaking = True
    try:
      sentences = re.split(r'(?<=[.!?])\s+', clean)
      sentences = [
        s.strip() for s in sentences
        if s.strip() and len(s.strip()) > 2
      ]

      if not sentences:
        return

      if len(sentences) == 1:
        asyncio.run(
          self._stream_and_play_edge_tts(sentences[0])
        )
      else:
        asyncio.run(
          self._stream_and_play_edge_tts(sentences[0])
        )

        if not self.stop_requested:
          rest = ' '.join(sentences[1:])
          asyncio.run(
            self._stream_and_play_edge_tts(rest)
          )

      print("[TTS] Playback complete")
    except Exception as e:
      print(f"[TTS] Edge-TTS error: {e}")
    finally:
      self.is_speaking = False

  def speak_sync(
    self,
    text: str,
    on_speech_start: Optional[callable] = None,
    on_speech_end: Optional[callable] = None
  ):
    if not text or not text.strip():
      return

    clean = self._clean_text(text)
    if not clean:
      return

    # --- DIAGNOSTIC: phase timing + overlap detection ---
    self._synth_seq += 1
    seq = self._synth_seq
    t_call = time.time()
    mem_before = _mem_probe()
    # Was a previous synthesis still in flight when this call arrived?
    overlapped = self._synth_active
    if overlapped:
      print(
        f"[TTS][DIAG#{seq}] OVERLAP: another synthesis was still active "
        f"when speak_sync() was called (prev seq {self._synth_active_seq})"
      )
    self._synth_active = True
    self._synth_active_seq = seq

    self.stop()
    t_after_stop = time.time()

    self.stop_requested = False
    self.stop_event.clear()
    self.speak_start_time = time.time()
    self._on_speech_start = on_speech_start
    self._on_speech_end = on_speech_end
    self._diag_seq_current = seq

    try:
      if not self.kokoro_ready.is_set():
        print("[TTS] Kokoro still warming up, waiting...")
        self.kokoro_ready.wait(timeout=30)
      t_after_ready = time.time()

      if self.kokoro_pipeline is not None and self.stream is not None:
        print(f"[TTS] Engine: Kokoro | Speaking: {clean[:60]}...")
        print(
          f"[TTS][DIAG#{seq}] phase: stop()={1000*(t_after_stop-t_call):.1f}ms "
          f"kokoro_ready_wait={1000*(t_after_ready-t_after_stop):.1f}ms | "
          f"chars={len(clean)} overlap={overlapped} | "
          f"RAM {mem_before['ram_pct']}% avail={mem_before['avail_mb']}MB "
          f"ws={mem_before['ws_mb']}MB faults={mem_before['faults']}"
        )
        success = self._speak_sync_kokoro(clean)
        mem_after = _mem_probe()
        if mem_before["faults"] >= 0 and mem_after["faults"] >= 0:
          d_faults = mem_after["faults"] - mem_before["faults"]
          print(
            f"[TTS][DIAG#{seq}] total={1000*(time.time()-t_call):.1f}ms | "
            f"page_faults_during_call={d_faults} | "
            f"ws {mem_before['ws_mb']}MB -> {mem_after['ws_mb']}MB | "
            f"RAM {mem_after['ram_pct']}% avail={mem_after['avail_mb']}MB"
          )
        if success:
          return
        print("[TTS] Kokoro playback failed, falling back to edge-tts")

      print(f"[TTS] Engine: edge-tts | Speaking: {clean[:60]}...")
      self._speak_sync_edge_tts(clean)
    finally:
      self._on_speech_start = None
      self._on_speech_end = None
      self._synth_active = False

  def stop(self):
    self.stop_requested = True
    self.stop_event.set()

    try:
      while not self.audio_queue.empty():
        try:
          self.audio_queue.get_nowait()
          self.audio_queue.task_done()
        except Exception:
          break
    except Exception:
      pass

    self.current_chunk = None
    self.chunk_offset = 0

    try:
      import pygame
      if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    except Exception:
      pass

    self.is_speaking = False

  def shutdown(self):
    self.stop()
    if self.stream is not None:
      try:
        self.stream.stop()
        self.stream.close()
      except Exception:
        pass
      self.stream = None

tts_engine = TTSEngine()
