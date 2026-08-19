import numpy as np
import sounddevice as sd
import threading
import queue
import time
import os
from pathlib import Path
from openwakeword.model import Model

class WakeWordDetector:
  def __init__(
    self,
    model_path: str,
    on_detected: callable,
    threshold: float = 0.3,
    sample_rate: int = 16000,
    chunk_size: int = 1280,
    get_is_listening: callable = None
  ):
    self.model_path = model_path
    self.on_detected = on_detected
    self.threshold = threshold
    self.sample_rate = sample_rate
    self.chunk_size = chunk_size
    self.is_running = False
    self.get_is_listening = get_is_listening  # Function to check if still processing
    
    if not os.path.exists(self.model_path):
        print(f"Warning: Wake word model not found at {self.model_path}. Voice features will be disabled.")
        self.model = None
        return
        
    try:
        # Load the ONNX model
        self.model = Model(
          wakeword_model_paths=[self.model_path],
          enable_speex_noise_suppression=False,
          vad_threshold=0
        )
        print(f"Wake word model loaded successfully")
        print(f"Models: {list(self.model.models.keys())}")
    except Exception as e:
        print(f"Warning: Failed to load wake word model: {e}")
        self.model = None
  
  def _audio_callback(
    self, indata, frames, time_info, status
  ):
    if status:
      pass # Ignore minor underflow warnings

    if not self.model or not self.is_running:
        return

    # Check if user is speaking (interrupt TTS)
    audio_level = np.sqrt(np.mean(indata**2))

    if audio_level > 0.02:  # Speaking threshold
      try:
        from .tts_engine import tts_engine
        if tts_engine.is_speaking:
          print("[INTERRUPT] User speaking - stopping TTS")
          tts_engine.stop()
          return  # Don't process as wake word yet
      except:
        pass

    # Check if voice manager is still processing previous command
    if self.get_is_listening and self.get_is_listening():
        return

    try:
        audio = (indata[:, 0] * 32768).astype(np.int16)
        prediction = self.model.predict(audio)

        # Check all model predictions
        for model_name, score in prediction.items():
          if score >= self.threshold:
            print(f"WAKE WORD DETECTED! Score: {score:.3f}")
            # Call on_detected directly - voice_manager will handle is_listening flag
            threading.Thread(target=self.on_detected, daemon=True).start()
            break
    except Exception as e:
        print(f"Error in wake word audio callback: {e}")
  
  def start(self):
    if self.is_running or not self.model:
      return
    self.is_running = True
    try:
        self.stream = sd.InputStream(
          samplerate=self.sample_rate,
          channels=1,
          dtype=np.float32,
          blocksize=self.chunk_size,
          callback=self._audio_callback
        )
        self.stream.start()
        print("Wake word detection started")
    except Exception as e:
        print(f"Warning: Failed to start microphone stream: {e}")
        self.is_running = False
        if hasattr(self, 'stream'):
            self.stream.close()
  
  def stop(self):
    self.is_running = False
    if hasattr(self, "stream"):
      try:
          self.stream.stop()
          self.stream.close()
      except Exception as e:
          print(f"Error stopping stream: {e}")
    print("Wake word detection stopped")
