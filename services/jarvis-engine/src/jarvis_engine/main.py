import asyncio
import contextlib
import sys
import time
import traceback

# Windows' default console encoding (cp1252) can't represent every
# character an LLM provider may legitimately return (e.g. Groq emitting a
# narrow no-break space, U+202F), which previously crashed any print() of
# that text with UnicodeEncodeError. Reconfigure here - at the top of the
# module that both `start.py` and uvicorn's --reload subprocess import
# first - so this holds regardless of how the app is launched or what
# PYTHONIOENCODING (if anything) the environment sets.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.database import init_db
from .core.config import settings, log_api_key_diagnostics

# Runs at import time (before the lifespan/DB/model-loading work below) so
# the masked key previews and any stale-system-env-var warning are the
# first thing visible in every startup log, not buried after several
# seconds of provider/model init output.
log_api_key_diagnostics()

async def _broadcast_audio_levels():
    """Drains audio_level_bus at a throttled ~12Hz and broadcasts the
    latest mic level over the voice WebSocket. Runs as its own asyncio
    task so the real-time audio callbacks in wake_word.py / speech_recorder
    only ever do an O(1) queue push - no awaiting, no broadcasting, no
    contention with the wake-word detection lock."""
    from .voice.audio_level_bus import get_latest_level
    from .api.routes import broadcast_voice_event, connected_clients

    while True:
        await asyncio.sleep(1 / 12)
        if not connected_clients:
            continue
        level = get_latest_level()
        if level is None:
            continue
        try:
            await broadcast_voice_event({
                "type": "audio_level",
                "level": round(level, 4)
            })
        except Exception:
            pass


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _t0 = time.time()
    await init_db()
    print(f"[TIMING] init_db: {time.time() - _t0:.2f}s")
    
    _t1 = time.time()
    from .plugins.placeholders import register_placeholders
    from .plugins.google_auth import init_google_oauth
    register_placeholders()
    init_google_oauth()
    print(f"[TIMING] init_plugins: {time.time() - _t1:.2f}s")

    _t1 = time.time()
    from .providers.manager import provider_manager, restore_preferred_provider

    # Restore the manually-selected provider PREFERENCE from the last
    # session (set via /provider/switch - see routes.py), before anything
    # below tries a provider or reports availability in cascade order.
    # This is a soft, reorder-only preference - distinct from
    # provider_override (config.py / fallback.py), which hard-locks the
    # cascade to a single provider with no fallback. Unset (fresh
    # install, or never manually switched) leaves provider_manager's
    # default Gemini -> OpenRouter -> Groq -> Ollama order untouched.
    restored = await restore_preferred_provider()
    if restored:
        print(f"[STARTUP] Restored preferred provider: {restored}")

    for provider in provider_manager.providers:
        _tp = time.time()
        available = await provider.is_available()
        print(f"Provider {provider.name}: {'available' if available else 'unavailable'} ({time.time() - _tp:.2f}s)")
    print(f"[TIMING] provider availability checks total: {time.time() - _t1:.2f}s")

    # `transformers` exposes its API via a _LazyModule whose __getattr__
    # resolves and caches each symbol (e.g. AlbertModel) on first access -
    # and that resolve-and-cache isn't guarded by a lock. Kokoro's loader
    # thread (`from kokoro import KPipeline` -> `from transformers import
    # AlbertModel`) and the memory embedding migration's thread (`from
    # sentence_transformers import SentenceTransformer` -> transformers'
    # own config loading) both first-touch transformers within
    # milliseconds of each other during startup, and racing that
    # __getattr__ intermittently raises "cannot import name 'AlbertModel'
    # from 'transformers'" (confirmed via a captured traceback - this is a
    # known thread-safety gap in transformers' lazy module, not a bug in
    # either loader). Warming the exact symbols each thread needs here,
    # synchronously and single-threaded, resolves and caches them as plain
    # instance attributes before either background thread starts, so
    # neither one ever hits the racy first-resolution path.
    _t_warm = time.time()

    def _warm_transformers():
        try:
            from transformers import AlbertModel  # noqa: F401 - kokoro's import chain
            from transformers.configuration_utils import PretrainedConfig  # noqa: F401 - sentence-transformers' import chain
            print(f"[STARTUP] transformers warmed ({time.time() - _t_warm:.2f}s)")
        except Exception as e:
            print(f"[STARTUP] transformers warmup failed (non-fatal): {e}")
            traceback.print_exc()

    await asyncio.to_thread(_warm_transformers)

    # --- Voice subsystem: TTS (Kokoro) and voice detection (Whisper +
    # wake word) are kicked off CONCURRENTLY here, but neither is awaited
    # to completion. Each one spawns its own background loader thread(s)
    # internally (see tts_engine.py / voice_manager.py) and returns almost
    # immediately, so lifespan finishes and FastAPI starts accepting
    # requests well before the heavy models are actually loaded. Use
    # GET /health's "voice_ready" field to check real readiness.
    _t2 = time.time()

    def _kickoff_tts():
        """Imports tts_engine, which spawns its own background loader
        thread for Kokoro and returns immediately - see tts_engine.py."""
        try:
            from .voice.tts_engine import tts_engine
            print("[STARTUP] TTS kicked off (Kokoro loading in background thread)")
        except Exception as e:
            print(f"[STARTUP] TTS init error: {e}")

    def _kickoff_voice():
        """Calls voice_manager.initialize(), which spawns background
        loader threads for Whisper + wake word and returns immediately -
        see voice_manager.py."""
        try:
            from .voice.voice_manager import voice_manager
            from .voice.transcription_handler import handle_transcription
            voice_manager.initialize(handle_transcription)
            print("Voice detection kicked off (Whisper + wake word loading in background threads)")
        except Exception as e:
            print(f"Voice init failed: {e}")

    await asyncio.gather(
        asyncio.to_thread(_kickoff_tts),
        asyncio.to_thread(_kickoff_voice),
    )
    print(f"[TIMING] voice subsystem kickoff (non-blocking): {time.time() - _t2:.2f}s")

    audio_level_task = asyncio.create_task(_broadcast_audio_levels())

    # Phase 7 M3: retrofit-embed any memory that predates the ChromaDB
    # index. Fire-and-forget like the voice subsystem above - it checks
    # what's already embedded before loading the (CPU-only) embedding
    # model, so on every restart after the first this finishes almost
    # instantly with no model load at all.
    async def _migrate_memory_embeddings():
        try:
            from .memory.memory_manager import memory_manager
            n = await memory_manager.migrate_embeddings()
            if n:
                print(f"[STARTUP] Embedded {n} pre-existing memories into ChromaDB")
        except Exception as e:
            print(f"[STARTUP] Memory embedding migration failed: {e}")

    asyncio.create_task(_migrate_memory_embeddings())

    print(f"[TIMING] TOTAL lifespan startup (models still loading in background): {time.time() - _t0:.2f}s")
    yield
    # Shutdown
    audio_level_task.cancel()
    from .voice.voice_manager import voice_manager
    voice_manager.shutdown()

app = FastAPI(
    title="JARVIS Engine",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
