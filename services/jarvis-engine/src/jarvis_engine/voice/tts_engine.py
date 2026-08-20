import asyncio
import os
import queue
import re
import tempfile
import threading
import time
from typing import Optional
import numpy as np

class TTSEngine:
  def __init__(self):
    self.is_speaking = False
    self.stop_requested = False
    self.speak_start_time = 0.0
    self.current_tmp_path = None
    
    self.audio_queue = queue.Queue()
    self.current_chunk: Optional[np.ndarray] = None
    self.chunk_offset = 0
    self.stop_event = threading.Event()
    self.stream = None

    # Persistent sounddevice OutputStream
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
      print("[TTS] Persistent sounddevice stream ready (24000Hz, mono, float32)")
    except Exception as e:
      self.stream = None
      print(f"[TTS] sounddevice OutputStream init error: {e}")

    # Primary TTS Engine: Kokoro
    self.kokoro_pipeline = None
    self.kokoro_voice = "am_michael"
    try:
      from jarvis_engine.core.config import settings
      self.kokoro_voice = getattr(settings, "TTS_KOKORO_VOICE", "am_michael")
    except Exception:
      pass

    try:
      from kokoro import KPipeline
      self.kokoro_pipeline = KPipeline(lang_code='a')
      print(f"[TTS] Kokoro TTS ready (voice: {self.kokoro_voice})")
      # Warmup model in background
      def _warmup():
        try:
          for _ in self.kokoro_pipeline("ready", voice=self.kokoro_voice, speed=1.0):
            pass
        except Exception:
          pass
      threading.Thread(target=_warmup, daemon=True).start()
    except (ImportError, RuntimeError, Exception) as e:
      self.kokoro_pipeline = None
      print(f"[TTS] Kokoro TTS init failed: {e}. Falling back to edge-tts.")

    print("[TTS] Andrew Multilingual voice ready (fallback)")

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

      def generator_thread():
        nonlocal gen_error, first_chunk_logged
        try:
          for result in self.kokoro_pipeline(clean, voice=self.kokoro_voice, speed=1.0):
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
              print(f"[TTS][Kokoro] Time to first audio: {ttfb:.1f}ms")

            self.audio_queue.put(audio_arr)
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

  def speak_sync(self, text: str):
    if not text or not text.strip():
      return

    clean = self._clean_text(text)
    if not clean:
      return

    self.stop()
    self.stop_requested = False
    self.stop_event.clear()
    self.speak_start_time = time.time()

    if self.kokoro_pipeline is not None and self.stream is not None:
      print(f"[TTS] Engine: Kokoro | Speaking: {clean[:60]}...")
      success = self._speak_sync_kokoro(clean)
      if success:
        return
      print("[TTS] Kokoro playback failed, falling back to edge-tts")

    print(f"[TTS] Engine: edge-tts | Speaking: {clean[:60]}...")
    self._speak_sync_edge_tts(clean)

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
