import numpy as np
import sounddevice as sd
import time

class SpeechRecorder:
  def __init__(
    self,
    sample_rate: int = 16000,
    silence_threshold: float = 0.01,
    silence_duration: float = 1.5,
    max_duration: float = 30.0
  ):
    self.sample_rate = sample_rate
    self.silence_threshold = silence_threshold
    self.silence_duration = silence_duration
    self.max_duration = max_duration
  
  def record(self) -> np.ndarray:
    """
    Record speech until silence detected.
    Returns numpy array of audio samples.
    """
    print("Listening for speech...")
    frames = []
    silent_frames = 0
    chunks_per_second = (self.sample_rate // 1024)
    max_silent = int(self.silence_duration * chunks_per_second)
    max_frames = int(self.max_duration * chunks_per_second)
    
    try:
        with sd.InputStream(
          samplerate=self.sample_rate,
          channels=1,
          dtype=np.float32,
          blocksize=1024
        ) as stream:
          while len(frames) < max_frames:
            chunk, _ = stream.read(1024)
            audio_chunk = chunk[:, 0]
            frames.append(audio_chunk)
            
            # Check for silence
            energy = np.sqrt(np.mean(audio_chunk**2))
            if energy < self.silence_threshold:
              silent_frames += 1
            else:
              silent_frames = 0
            
            if (silent_frames >= max_silent and len(frames) > chunks_per_second):
              # Got at least 1 second of audio and detected silence
              break
        
        if frames:
            audio = np.concatenate(frames)
            print(f"Recorded {len(audio)/self.sample_rate:.1f}s")
            return audio
    except Exception as e:
        print(f"Warning: Failed to record speech: {e}")
        
    return np.array([])
