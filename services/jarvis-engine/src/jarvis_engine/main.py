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

    # Auto-start voice detection
    try:
        from .voice.voice_manager import voice_manager

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

                    # Then speak
                    try:
                        tts_engine.speak_sync(direct_result)
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
                                tts_engine.speak_sync(ai_response)
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
