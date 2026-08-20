import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.database import init_db
from .core.config import settings

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    from .providers.manager import provider_manager
    for provider in provider_manager.providers:
        available = await provider.is_available()
        print(f"Provider {provider.name}: {'available' if available else 'unavailable'}")

    # Pre-load TTS engine at startup
    try:
        from .voice.tts_engine import tts_engine
        print("[STARTUP] Andrew Multilingual TTS ready")
    except Exception as e:
        print(f"[STARTUP] TTS init error: {e}")

    # Auto-start voice detection
    try:
        from .voice.voice_manager import voice_manager
        import re

        def clean_text_for_tts(text: str) -> str:
            """Strip UI_ACTION tags and markdown formatting for clean TTS output"""
            if not text:
                return ""

            # Strip UI_ACTION tags
            clean = re.sub(r'\[UI_ACTION:[^\]]*\]', '', text).strip()

            # Strip markdown formatting
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)  # Bold
            clean = re.sub(r'\*(.+?)\*', r'\1', clean)  # Italic
            clean = re.sub(r'#{1,6}\s', '', clean)  # Headers
            clean = re.sub(r'`(.+?)`', r'\1', clean)  # Inline code
            clean = re.sub(r'```[\s\S]*?```', '', clean)  # Code blocks

            return clean.strip()

        def on_transcription(text: str, direct_result: str = None):
            print(f"[VOICE COMMAND] {text}")

            # Direct command already executed - just broadcast and speak
            if direct_result:
                print(f"[VOICE DIRECT] {direct_result}")
                import threading

                def speak_and_broadcast():
                    import requests
                    from jarvis_engine.voice.tts_engine import tts_engine

                    # Broadcast to UI first
                    try:
                        requests.post(
                            "http://localhost:8765/voice/input",
                            json={
                                "text": text,
                                "direct_response": direct_result
                            },
                            timeout=10
                        )
                    except Exception as e:
                        print(f"Broadcast error: {e}")

                    # Then speak (clean text)
                    try:
                        clean_result = clean_text_for_tts(direct_result)
                        if clean_result and len(clean_result) > 3:
                            tts_engine.speak_sync(clean_result)
                    except Exception as e:
                        print(f"TTS error: {e}")

                t = threading.Thread(target=speak_and_broadcast, daemon=True)
                t.start()
                return

            # LLM pipeline - speak the response
            def send_and_speak():
                import requests
                from jarvis_engine.voice.tts_engine import tts_engine

                try:
                    response = requests.post(
                        "http://localhost:8765/voice/input",
                        json={"text": text},
                        timeout=60
                    )
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get("response", "")
                        if ai_response:
                            print(f"[JARVIS SPEAKING] {ai_response}")
                            try:
                                clean_response = clean_text_for_tts(ai_response)
                                if clean_response and len(clean_response) > 3:
                                    tts_engine.speak_sync(clean_response)
                            except Exception as e:
                                print(f"TTS error: {e}")
                except Exception as e:
                    print(f"[VOICE ERROR] {e}")

            import threading
            t = threading.Thread(target=send_and_speak, daemon=True)
            t.start()

        voice_manager.initialize(on_transcription)
        print("Voice detection auto-started")
    except Exception as e:
        print(f"Voice init failed: {e}")

    yield
    # Shutdown
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
