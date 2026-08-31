import contextlib
import os
import threading
import time

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

from .audio_level_bus import push_level


@contextlib.contextmanager
def _force_cpu_onnx():
    """Temporarily strip CUDAExecutionProvider from onnxruntime sessions.

    openWakeWord hardcodes providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
    for its melspec/embedding preprocessor models with no way to override this
    via its public API. See USE_GPU_WAKEWORD in core/config.py for why this
    stays CPU by default (tiny model, already fast, saves VRAM for
    Whisper/Kokoro on a 4GB card)."""
    import onnxruntime as ort

    orig_init = ort.InferenceSession.__init__

    def _patched_init(self, *args, **kwargs):
        if kwargs.get("providers"):
            kwargs["providers"] = [
                p for p in kwargs["providers"] if p != "CUDAExecutionProvider"
            ]
        return orig_init(self, *args, **kwargs)

    ort.InferenceSession.__init__ = _patched_init
    try:
        yield
    finally:
        ort.InferenceSession.__init__ = orig_init


class WakeWordDetector:
    def __init__(
        self,
        model_path: str,
        on_detected: callable,
        threshold: float = None,
        sample_rate: int = 16000,
        chunk_size: int = 1280,
        get_is_listening: callable = None,
        set_is_listening: callable = None,
        cooldown_seconds: float = 2.0,
        tts_mute_buffer_seconds: float = None,
        get_tts_state: callable = None,
        tts_interrupt_grace_seconds: float = None,
        tts_interrupt_level_threshold: float = None,
        get_tts_playback_state: callable = None,
        score_log_floor: float = None,
    ):
        from ..core.config import settings

        self.model_path = model_path
        self.on_detected = on_detected
        # Detection score cutoff. See WAKE_WORD_THRESHOLD in core/config.py for
        # the sensitivity vs. false-trigger tradeoff this controls.
        if threshold is None:
            threshold = settings.WAKE_WORD_THRESHOLD
        self.threshold = threshold
        # Near-miss visibility: log scores that register but fall short of the
        # threshold, so a wake word that fails to fire is diagnosable instead
        # of silent. See WAKE_WORD_SCORE_LOG_FLOOR in core/config.py.
        if score_log_floor is None:
            score_log_floor = settings.WAKE_WORD_SCORE_LOG_FLOOR
        self.score_log_floor = score_log_floor
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_running = False
        self.get_is_listening = (
            get_is_listening  # Function to check if still processing
        )
        self.set_is_listening = (
            set_is_listening  # Function to set listening state synchronously
        )
        self._detection_lock = threading.Lock()
        self.last_detection_time = 0.0
        self.cooldown_seconds = cooldown_seconds

        # How long to stay muted after TTS stops (room echo / speaker tail).
        if tts_mute_buffer_seconds is None:
            from ..core.config import settings

            tts_mute_buffer_seconds = settings.WAKE_WORD_TTS_MUTE_BUFFER_SECONDS
        self.tts_mute_buffer_seconds = tts_mute_buffer_seconds
        # Returns (is_speaking, last_speech_end_time). Injectable so tests can
        # drive the mute gate without importing the heavy TTS singleton.
        self.get_tts_state = get_tts_state

        # Barge-in tuning. Both are config-backed so they can be retuned
        # without a code change; see core/config.py.
        if tts_interrupt_grace_seconds is None:
            tts_interrupt_grace_seconds = settings.TTS_INTERRUPT_GRACE_SECONDS
        self.tts_interrupt_grace_seconds = tts_interrupt_grace_seconds
        if tts_interrupt_level_threshold is None:
            tts_interrupt_level_threshold = settings.TTS_INTERRUPT_LEVEL_THRESHOLD
        self.tts_interrupt_level_threshold = tts_interrupt_level_threshold
        # Returns (is_speaking, last_speech_start_time). Injectable so tests can
        # drive barge-in without importing the heavy TTS singleton. Kept separate
        # from get_tts_state, which reports speech END for the mute gate.
        self.get_tts_playback_state = get_tts_playback_state

        self._muted = False
        self._flushing = False

        if not os.path.exists(self.model_path):
            print(
                f"Warning: Wake word model not found at {self.model_path}. Voice features will be disabled."
            )
            self.model = None
            return

        _t = time.time()
        try:
            # Load the ONNX model. The wakeword classification head always runs
            # on CPUExecutionProvider (openWakeWord hardcodes this); only the
            # melspec/embedding preprocessor models are eligible for CUDA. Gated
            # by USE_GPU_WAKEWORD - default off, see core/config.py.
            use_gpu_wakeword = getattr(settings, "USE_GPU_WAKEWORD", False)
            if use_gpu_wakeword:
                self.model = Model(
                    wakeword_model_paths=[self.model_path],
                    enable_speex_noise_suppression=False,
                    vad_threshold=0,
                )
            else:
                with _force_cpu_onnx():
                    self.model = Model(
                        wakeword_model_paths=[self.model_path],
                        enable_speex_noise_suppression=False,
                        vad_threshold=0,
                    )
            provider = self.model.preprocessor.onnx_execution_provider
            print(
                f"Wake word model loaded successfully "
                f"[provider={provider}] [{time.time() - _t:.2f}s]"
            )
            print(f"Models: {list(self.model.models.keys())}")
        except Exception as e:
            print(
                f"Warning: Failed to load wake word model: {e} [{time.time() - _t:.2f}s]"
            )
            self.model = None

    def _is_tts_muted(self) -> bool:
        """True while JARVIS is speaking, and for tts_mute_buffer_seconds
        afterwards to cover room echo and speaker decay."""
        if self.get_tts_state is not None:
            is_speaking, last_end = self.get_tts_state()
        else:
            try:
                from .tts_engine import tts_engine
            except Exception:
                return False
            is_speaking = tts_engine.is_speaking
            last_end = getattr(tts_engine, "last_speech_end_time", 0.0)

        if is_speaking:
            return True

        if last_end and (time.time() - last_end) < self.tts_mute_buffer_seconds:
            return True

        return False

    def _get_tts_playback_state(self):
        """Returns (is_speaking, last_speech_start_time).

        Anchored on when audio playback actually began, NOT on when speak() was
        called - the two can be seconds apart while Kokoro warms up.
        """
        if self.get_tts_playback_state is not None:
            return self.get_tts_playback_state()

        try:
            from .tts_engine import tts_engine
        except Exception:
            return False, 0.0

        return (
            tts_engine.is_speaking,
            getattr(tts_engine, "last_speech_start_time", 0.0),
        )

    def _start_buffer_flush(self):
        """Clear the model's stale internal audio/feature history in a
        background thread (never in the audio callback, which must stay
        fast). Predictions are suppressed via self._flushing until done."""
        if self._flushing:
            return
        self._flushing = True

        def _flush():
            try:
                self.model.reset()  # clears the prediction/score buffer
                # Push silence through to evict pre-mute audio from the ~10s
                # feature buffer, so it can't re-trigger once we resume.
                silence = np.zeros(self.sample_rate * 2, dtype=np.int16)
                self.model.predict(silence)
                self.model.reset()
            except Exception as e:
                print(f"[WAKE] Buffer flush error: {e}")
            finally:
                self._flushing = False

        threading.Thread(target=_flush, daemon=True, name="wakeword-flush").start()

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass  # Ignore minor underflow warnings

        if not self.model or not self.is_running:
            return

        # BARGE-IN (INTERRUPT) CHECK
        #
        # *** ARCHITECTURE NOTE ***
        # This block MUST remain OUTSIDE (i.e. before) the _is_tts_muted() gate
        # below. The mute gate suppresses model.predict() to stop JARVIS
        # triggering on its own voice — but the interrupt level-check needs to
        # keep running during that same window so genuine user speech can barge
        # in. Moving this block inside the mute gate would silently disable
        # interruption entirely during TTS, which is the opposite of what we
        # want. If you ever refactor the early-return logic here, verify that
        # the interrupt path still executes while is_tts_muted() is True.
        #
        # Lets the user talk over a long response. Only meaningful while TTS is
        # actually speaking; when it isn't, there is nothing to interrupt.
        #
        # Two guards keep JARVIS's own speaker echo from cutting off its own
        # speech (the previous behaviour: "Yes sir?" died almost instantly):
        #
        #  1. Grace period, measured from when playback ACTUALLY started. The
        #     old check measured from speak_start_time - stamped when speak()
        #     was called, before the Kokoro warmup and time-to-first-audio - so
        #     the window was largely spent before a single sample was audible.
        #  2. A level threshold set above observed self-echo (0.098 / 0.119)
        #     rather than below it.
        #
        # Both values are config-tunable; see core/config.py for the tradeoff.
        audio_level = np.sqrt(np.mean(indata**2))
        # Waveform feed for the UI mic indicator. O(1) non-blocking queue push -
        # the actual WebSocket broadcast happens off a separate background task
        # (see main.py), never in this real-time callback. Pushed unconditionally
        # (even while muted/cooling down) so the indicator reflects that the mic
        # is always live, not just when a detection is possible.
        push_level(min(1.0, float(audio_level)))

        try:
            is_speaking, playback_start = self._get_tts_playback_state()
            if is_speaking:
                elapsed = time.time() - playback_start if playback_start else 0.0
                if elapsed < self.tts_interrupt_grace_seconds:
                    # Too early to be a genuine interrupt; almost certainly our own
                    # audio. Skip the check entirely for this frame.
                    pass
                elif audio_level > self.tts_interrupt_level_threshold:
                    from .tts_engine import tts_engine

                    print(
                        f"[INTERRUPT] Level: {audio_level:.3f} "
                        f"(threshold {self.tts_interrupt_level_threshold:.3f}, "
                        f"{elapsed:.2f}s into playback) - Stopping TTS"
                    )
                    tts_engine.stop()
                    return  # Don't process as wake word yet
        except Exception:
            pass

        # TTS MUTE GATE: never feed JARVIS's own audio into the wake-word
        # model. While TTS is speaking - and for a short buffer afterwards to
        # cover room echo / speaker decay - skip prediction entirely for this
        # frame. Without this the model itself produces genuine high-confidence
        # (0.99+) detections on JARVIS's own voice, causing an endless
        # self-triggering loop with no user input.
        #
        # This is deliberately separate from the interrupt-level heuristic
        # above: that one lets a user barge in over a long response; this one
        # is about the model never seeing our own output as input at all.
        if self._is_tts_muted():
            if not self._muted:
                print("[WAKE] Muted during TTS playback (+buffer)")
                self._muted = True
            return

        if self._muted:
            # Leaving the mute window. openWakeWord keeps ~10s of internal
            # feature history, which still holds pre-mute audio (including the
            # user's own original wake word). Flush it before resuming, or that
            # stale context can immediately re-fire on its own.
            self._muted = False
            self._start_buffer_flush()

        # Predictions stay suppressed until the flush completes.
        if self._flushing:
            return

        # Check if voice manager is still processing previous command
        if self.get_is_listening and self.get_is_listening():
            return

        # Check cooldown after previous detection
        if time.time() - self.last_detection_time < self.cooldown_seconds:
            return

        try:
            audio = (indata[:, 0] * 32768).astype(np.int16)
            prediction = self.model.predict(audio)

            # Check all model predictions
            for model_name, score in prediction.items():
                # Near-miss logging: makes "why didn't it fire?" answerable.
                if (
                    self.score_log_floor
                    and score >= self.score_log_floor
                    and score < self.threshold
                ):
                    print(
                        f"[WAKE] Near miss: {score:.3f} "
                        f"(threshold {self.threshold:.3f})"
                    )
                if score >= self.threshold:
                    # Atomic check-and-set inside lock BEFORE spawning thread (prevents TOCTOU duplicate dispatches)
                    with self._detection_lock:
                        if self.get_is_listening and self.get_is_listening():
                            return
                        if (
                            time.time() - self.last_detection_time
                            < self.cooldown_seconds
                        ):
                            return

                        self.last_detection_time = time.time()
                        if self.set_is_listening:
                            self.set_is_listening(True)

                    print(f"WAKE WORD DETECTED! Score: {score:.3f}")
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
                callback=self._audio_callback,
            )
            self.stream.start()
            print("Wake word detection started")
        except Exception as e:
            print(f"Warning: Failed to start microphone stream: {e}")
            self.is_running = False
            if hasattr(self, "stream"):
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
