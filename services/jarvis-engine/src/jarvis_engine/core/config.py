import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the .env file this Settings() reads (SettingsConfigDict
# below uses a bare relative "env_file", which only resolves correctly when
# the process CWD happens to be this directory - this absolute path is used
# purely for the diagnostics below, which must find the real .env
# regardless of CWD).
_ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"

# API key settings worth a masked startup preview and a stale-system-env-var
# check. Confirmed live bug this guards against: a Windows user/system
# environment variable named GEMINI_API_KEY, set independently of .env and
# holding an old, already-rotated key. pydantic-settings resolves real OS
# environment variables with HIGHER priority than the .env file by design -
# so editing .env silently did nothing while that stale system var existed,
# and there was no signal anywhere that this was happening.
_API_KEY_FIELDS = [
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
    "CEREBRAS_API_KEY",
]

class Settings(BaseSettings):
    JARVIS_HOST: str = "localhost"
    JARVIS_PORT: int = 8765
    OLLAMA_HOST: str = ""
    OLLAMA_MODEL: str = "phi4-mini"
    OLLAMA_AVAILABILITY_TIMEOUT: float = 10.0
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-4-27b-it:free"
    TAVILY_API_KEY: str = ""
    TAVILY_MAX_RESULTS: int = 5
    SEARCH_PROVIDER: str = "tavily"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    CEREBRAS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    WEATHER_DEFAULT_LOCATION: str = "Chennai"
    WAKE_WORD_MODEL_PATH: str = "models/wake_up_jarvis.onnx"
    DB_PATH: str = "data/jarvis.db"
    # Persistent ChromaDB store for memory embeddings (Phase 7 M3) - lives
    # next to jarvis.db under data/, SQLite stays the source of truth for
    # content/metadata, this is purely a similarity-search index.
    CHROMA_PATH: str = "data/chroma"
    VERSION: str = "0.1.0"

    # GPU acceleration (NVIDIA CUDA) for the voice pipeline. Set false to
    # force everything back onto CPU without a code change - e.g. if the
    # GPU build proves unstable or another process needs the VRAM.
    USE_GPU: bool = True
    # Wake-word (openWakeWord) inference is tiny and already fast on CPU
    # (sub-second model load, real-time detection). On a 4GB card it's not
    # worth spending VRAM on - keeping it on CPU leaves more headroom for
    # Whisper + Kokoro. Independent of USE_GPU so it can be flipped on its
    # own if a future card has VRAM to spare.
    USE_GPU_WAKEWORD: bool = False

    # How long voice_manager.shutdown() waits for the Whisper / wake-word
    # loader threads to finish before tearing down. Shutdown used to race
    # them, which left an unowned mic stream and crashed the interpreter.
    # Generous enough to cover a cold faster-whisper model download, and
    # bounded so shutdown can never hang outright.
    VOICE_SHUTDOWN_LOADER_TIMEOUT: float = 30.0

    # Skip the voice subsystem entirely at startup: no Whisper load, no
    # wake-word model, no microphone stream. Set by the test suite (see
    # tests/conftest.py) so running the app's real lifespan doesn't
    # download models from HuggingFace or contend for the OS audio
    # device. Never set this in normal operation - voice simply won't work.
    VOICE_DISABLED: bool = False

    # TTS Configuration
    EDGE_TTS_VOICE: str = "en-US-AndrewMultilingualNeural"
    EDGE_TTS_RATE: str = "+5%"
    TTS_KOKORO_VOICE: str = "am_michael"

    # Seconds to keep the wake-word model muted AFTER TTS stops speaking.
    # Covers room echo / speaker decay tail so JARVIS's own audio can never
    # be fed into the wake-word model and re-trigger it.
    WAKE_WORD_TTS_MUTE_BUFFER_SECONDS: float = 0.4

    # openWakeWord prediction score required to fire a detection.
    #
    # TRADEOFF - this is the precision/recall dial for a keyword-spotting
    # model, and no single value "solves" it:
    #   lower  -> triggers reliably at normal conversational volume, but is
    #             more prone to false triggers from background noise, a TV,
    #             or nearby conversation.
    #   higher -> far fewer false triggers, but requires unnaturally loud
    #             or over-enunciated speech to reach the score.
    # The previous value was 0.3, and in practice only shouted speech got
    # over it (observed successful detections scored 0.751 / 0.780). Note
    # that 0.5 would be a REGRESSION here - it is higher than 0.3 and would
    # demand even louder speech. Lowering to 0.2 is the direction that
    # actually buys sensitivity at conversational volume.
    WAKE_WORD_THRESHOLD: float = 0.2

    # Log every prediction at or above this score, even when it does not
    # reach WAKE_WORD_THRESHOLD. Without this, a wake word that fails to
    # trigger is silent in the logs and there is no way to tell "the model
    # scored 0.18, nudge the threshold" apart from "the model scored 0.01,
    # the mic gain is the real problem". Set to 0 to disable.
    WAKE_WORD_SCORE_LOG_FLOOR: float = 0.05

    # Barge-in (interrupt) tuning for the wake-word audio callback.
    #
    # Grace period: for this long after audio playback actually STARTS,
    # the interrupt check is skipped entirely. Short utterances such as
    # "Yes sir?" are almost never genuinely interrupted this early, while
    # self-echo risk from our own speaker is at its highest.
    TTS_INTERRUPT_GRACE_SECONDS: float = 0.8

    # Mic RMS level required to count as a genuine user barge-in once the
    # grace period above has elapsed. Raised from the previous 0.08, which
    # sat below JARVIS's own speaker echo (observed at 0.098 and 0.119) and
    # so cut its own speech off. Keep this meaningfully above typical
    # self-echo but below deliberate speech.
    TTS_INTERRUPT_LEVEL_THRESHOLD: float = 0.18

    # Phrase-based interrupts: checked against the FINAL Whisper transcript
    # of an open recording window (see voice_manager.py), case-insensitively,
    # matching if the transcript IS the phrase or STARTS WITH it followed by
    # a word boundary (so "stop please" / "wake up jarvis wake up jarvis"
    # still count, but "stopwatch" doesn't). This is separate from - and
    # complements - TTS_INTERRUPT_LEVEL_THRESHOLD above: that one detects
    # ANY sufficiently loud speech as "interrupt me", this one recognizes
    # SPECIFIC phrases regardless of loudness and decides what to do next.
    #
    # WAKE_PHRASE is split out from INTERRUPT_PHRASES because it behaves
    # differently on match: it starts a genuinely fresh wake cycle (new
    # "Yes sir?" + new recording window), the same effect saying it to the
    # wake-word MODEL would have - that model is deliberately muted during
    # TTS (prevents self-echo re-triggering), so this transcript-level
    # check is the only way to reach the same effect while JARVIS is
    # talking. The rest of INTERRUPT_PHRASES just stop playback and return
    # to idle/listening - no new acknowledgment.
    WAKE_PHRASE: str = "wake up jarvis"
    INTERRUPT_PHRASES: list[str] = ["stop", "wait", "cancel", "never mind", "hold on"]

    # Continuous conversation mode: once a wake-word session's first command
    # has been answered, JARVIS keeps listening directly for follow-up
    # commands (no repeated "wake up jarvis") until an explicit exit phrase
    # or this many seconds of silence. See voice_manager.py's
    # continue_conversation() / _on_continuous_timeout() for the state
    # machine this drives. Session-only - resets to inactive on every
    # restart, never persisted.
    CONTINUOUS_MODE_TIMEOUT_SECONDS: float = 50.0

    # Checked against the FINAL transcript, using the SAME phrase-matching
    # mechanism as WAKE_PHRASE/INTERRUPT_PHRASES above (case-insensitive,
    # apostrophe/punctuation-insensitive - "that's all jarvis" also matches
    # "thats all jarvis"), and BEFORE INTERRUPT_PHRASES/normal command
    # handling - see match_continuous_exit_phrase() in voice_manager.py.
    # Includes both the original "<phrase> jarvis" / "jarvis <phrase>" forms
    # AND bare natural variants without "jarvis" attached - CONFIRMED
    # INCIDENT: a user said "Go to sleep." (no "jarvis"), it matched
    # nothing here, fell through to the LLM, which fabricated "Understood.
    # Ending session." even though continuous mode never actually exited -
    # see voice_manager.py's _looks_like_uncertain_exit_intent() for the
    # additional, phrase-list-independent defense against exactly this
    # class of gap (an exit-sounding phrase that isn't in this list at
    # all, not just a wording variant of one that is).
    CONTINUOUS_MODE_EXIT_PHRASES: list[str] = [
        "stop listening jarvis",
        "jarvis go to sleep",
        "thats all jarvis",
        "jarvis i will talk to you later",
        "go to sleep",
        "stop listening",
        "thats all",
    ]

    # Personality and Modifier Defaults
    PERSONALITY_MODE: str = "assistant"
    MODIFIER: str = "none"
    CONVERSATION_DELETE_PIN: str = "0523"
    # How the LLM addresses the user - "sir" matches the prior hardcoded
    # behavior exactly. Empty string means no address term at all.
    ADDRESS_PREFERENCE: str = "sir"

    # Daily briefing (Phase 6 M3): prepended to the first response of each
    # calendar day. "" means never briefed yet.
    LAST_BRIEFING_DATE: str = ""
    DAILY_BRIEFING_ENABLED: str = "true"

    # Provider fallback controls. "" (empty) means no override - the normal
    # Gemini -> OpenRouter -> Groq -> Ollama cascade applies. When set, ONLY
    # that provider is tried; a failure is reported, never silently
    # substituted. fallback_mode "ask" pauses the cascade on the first
    # failure and asks the user which provider to try next, instead of
    # auto-advancing to the next one in line.
    PROVIDER_OVERRIDE: str = ""
    FALLBACK_MODE: str = "auto"

    # Preferred provider (distinct from PROVIDER_OVERRIDE above): set by a
    # manual /provider/switch, this only reorders the normal cascade so the
    # chosen provider is tried FIRST on restart - it does not disable
    # fallback to the others if it's unavailable, unlike PROVIDER_OVERRIDE's
    # hard lock. Empty means no preference recorded yet - use the default
    # Gemini -> OpenRouter -> Groq -> Ollama order. See main.py's lifespan
    # startup, where this is read back and applied via
    # provider_manager.set_active_provider() before the app serves requests.
    PREFERRED_PROVIDER: str = ""
    PREFERRED_MODEL: str = ""

    # Gate prints that include raw user content (email bodies, extracted
    # memory text). Default False — set to true only for local debugging.
    # All operational/metadata prints are unaffected by this flag.
    DEBUG_LOG_CONTENT: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()


def _mask(value: str) -> str:
    """First 6 / last 6 characters only - never log a full key."""
    if not value:
        return "(not set)"
    if len(value) <= 12:
        return "*" * len(value)
    return f"{value[:6]}...{value[-6:]}"


def log_api_key_diagnostics() -> None:
    """Prints a masked preview of every API key setting actually in effect,
    and loudly warns if a real OS/system environment variable is silently
    overriding what .env says - pydantic-settings (and the underlying
    python-dotenv load) resolves real environment variables with HIGHER
    priority than .env file values, so a stale system-level env var makes
    every .env edit a no-op with zero visible signal. Call this once at
    startup, right after `settings` is constructed.
    """
    env_file_values = dotenv_values(_ENV_FILE_PATH) if _ENV_FILE_PATH.exists() else {}

    print("[CONFIG] API key sources in effect:")
    for field in _API_KEY_FIELDS:
        effective_value = getattr(settings, field, "")
        print(f"[CONFIG]   {field} = {_mask(effective_value)}")

        os_value = os.environ.get(field)
        env_file_value = env_file_values.get(field)
        if os_value and os_value != (env_file_value or ""):
            print(
                f"[CONFIG] WARNING: {field} is set as a system environment "
                f"variable ({_mask(os_value)}) and differs from .env "
                f"({_mask(env_file_value or '')}) - the system value will be "
                f"used no matter what .env says. Run "
                f"[System.Environment]::SetEnvironmentVariable('{field}', "
                f"$null, 'User') to remove it if this is unintended, then "
                f"restart the engine."
            )
