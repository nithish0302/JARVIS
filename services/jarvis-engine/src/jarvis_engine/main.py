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
        
    yield
    # Shutdown
    pass

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
