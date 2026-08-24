from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    JARVIS_HOST: str = "localhost"
    JARVIS_PORT: int = 8765
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi4-mini"
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
