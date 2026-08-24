import numpy as np
import sounddevice as sd
import threading
import time
from typing import Optional
from .audio_level_bus import push_level

class SpeechRecorder:
  def __init__(
    self,
    sample_rate: int = 16000,
    silence_threshold: float = 0.01,
    silence_duration: float = 1.5,
    wait_for_speech_timeout: float = 6.0,
    max_duration: float = 30.0
  ):
    self.sample_rate = sample_rate
    self.silence_threshold = silence_threshold
    self.silence_duration = silence_duration
    self.wait_for_speech_timeout = wait_for_speech_timeout
    self.max_duration = max_duration

  def record(self, tts_finished_event: Optional[threading.Event] = None) -> np.ndarray:
    """
    Record speech until trailing silence detected. The mic stream opens
    immediately regardless of tts_finished_event, so a fast talker who
    starts before the wake-word acknowledgement finishes is still caught
    by the has_started_speaking check below.

    wait_for_speech_timeout only starts counting down once tts_finished_event
    is set (or immediately if no event is given) - i.e. once the "Yes sir?"
    playback has genuinely finished, not from whenever this method happened
    to be called. Without this, a slow TTS synthesis call silently eats into
    the caller's real window to respond, since the countdown was previously
    ticking in parallel with playback still in progress.

    Applies wait_for_speech_timeout before speech starts,
    and silence_duration trailing silence after speech starts.
    Returns numpy array of audio samples.
    """
    print("Listening for speech...")
    frames = []
    has_started_speaking = False
    silent_frames = 0
    wait_frames = 0  # only advances once TTS playback has finished
    chunks_per_second = (self.sample_rate // 1024)
    max_silent = int(self.silence_duration * chunks_per_second)
    max_wait_frames = int(self.wait_for_speech_timeout * chunks_per_second)
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

            energy = np.sqrt(np.mean(audio_chunk**2))
            # Same waveform feed as wake_word.py, so the mic indicator
            # doesn't go dead when idle-listening hands off to active
            # recording.
            push_level(min(1.0, float(energy)))

            if not has_started_speaking:
              if energy >= self.silence_threshold:
                has_started_speaking = True
                silent_frames = 0
              elif tts_finished_event is None or tts_finished_event.is_set():
                wait_frames += 1
                if wait_frames >= max_wait_frames:
                  print("[VOICE] No speech detected within timeout")
                  return np.array([])
            else:
              if energy < self.silence_threshold:
                silent_frames += 1
              else:
                silent_frames = 0
              
              if silent_frames >= max_silent:
                # User finished speaking and trailing silence detected
                break
        
        if frames and has_started_speaking:
            audio = np.concatenate(frames)
            print(f"Recorded {len(audio)/self.sample_rate:.1f}s")
            return audio
    except Exception as e:
        print(f"Warning: Failed to record speech: {e}")
        
    return np.array([])
