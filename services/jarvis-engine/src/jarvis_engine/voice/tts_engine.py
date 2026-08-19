import edge_tts
import asyncio
import pygame
import io
import threading
import numpy as np

class TTSEngine:
  def __init__(self):
    self.voice = "en-GB-RyanNeural"
    self.is_speaking = False
    self.stop_requested = False
    pygame.mixer.init(frequency=22050)
    print("TTS engine initialized")

  async def speak(self, text: str):
    if not text or not text.strip():
      return

    # Stop any current speech
    self.stop()
    self.is_speaking = True
    self.stop_requested = False

    try:
      # Generate speech with edge-tts
      communicate = edge_tts.Communicate(
        text=text,
        voice=self.voice,
        rate="+10%",  # Slightly faster
        volume="+0%"
      )

      # Collect audio data
      audio_data = b""
      async for chunk in communicate.stream():
        if chunk["type"] == "audio":
          if self.stop_requested:
            break
          audio_data += chunk["data"]

      if not self.stop_requested and audio_data:
        # Play via pygame
        audio_io = io.BytesIO(audio_data)
        pygame.mixer.music.load(audio_io)
        pygame.mixer.music.play()

        # Wait for completion or interrupt
        while pygame.mixer.music.get_busy():
          if self.stop_requested:
            pygame.mixer.music.stop()
            break
          await asyncio.sleep(0.1)

    except Exception as e:
      print(f"TTS error: {e}")
    finally:
      self.is_speaking = False

  def stop(self):
    self.stop_requested = True
    if self.is_speaking:
      try:
        pygame.mixer.music.stop()
      except:
        pass
    self.is_speaking = False

  def speak_sync(self, text: str):
    asyncio.run(self.speak(text))

tts_engine = TTSEngine()
