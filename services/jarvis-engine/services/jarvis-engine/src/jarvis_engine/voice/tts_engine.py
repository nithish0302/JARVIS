import asyncio
import os
import re
import tempfile
import time
import winsound

class TTSEngine:
  def __init__(self):
    self.is_speaking = False
    self.stop_requested = False
    self.speak_start_time = 0
    self.current_tmp_path = None
    print("[TTS] Andrew Multilingual voice ready")

  def _clean_text(self, text: str) -> str:
    text = re.sub(
      r'\[UI_ACTION:[^\]]*\]', '', text
    )
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'http\S+', '', text)
    text = ' '.join(text.split())
    return text.strip()

  async def _generate_audio(
    self, text: str
  ) -> str | None:
    try:
      import edge_tts
      from jarvis_engine.core.config import settings

      voice = getattr(
        settings,
        'EDGE_TTS_VOICE',
        'en-US-AndrewMultilingualNeural'
      )
      rate = getattr(
        settings, 'EDGE_TTS_RATE', '+5%'
      )

      communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate
      )

      tmp = tempfile.NamedTemporaryFile(
        suffix='.mp3', delete=False
      )
      tmp_path = tmp.name
      tmp.close()

      await communicate.save(tmp_path)
      print(f"[TTS] Audio generated: {tmp_path}")
      return tmp_path

    except Exception as e:
      print(f"[TTS] Generation error: {e}")
      return None

  def speak_sync(self, text: str):
    if not text or not text.strip():
      return

    self.stop()
    self.is_speaking = True
    self.stop_requested = False
    self.speak_start_time = time.time()

    try:
      clean = self._clean_text(text)
      if not clean:
        return

      print(f"[TTS] Speaking: {clean[:60]}...")

      # Generate audio
      tmp_path = asyncio.run(
        self._generate_audio(clean)
      )

      if not tmp_path or self.stop_requested:
        return

      self.current_tmp_path = tmp_path

      # Play with winsound (thread-safe)
      print("[TTS] Playing audio...")
      winsound.PlaySound(
        tmp_path,
        winsound.SND_FILENAME
      )
      print("[TTS] Playback complete")

    except Exception as e:
      print(f"[TTS] speak_sync error: {e}")
    finally:
      self.is_speaking = False
      if self.current_tmp_path:
        try:
          os.unlink(self.current_tmp_path)
        except:
          pass
        self.current_tmp_path = None

  def stop(self):
    self.stop_requested = True
    try:
      winsound.PlaySound(None, winsound.SND_PURGE)
    except:
      pass
    self.is_speaking = False

tts_engine = TTSEngine()
