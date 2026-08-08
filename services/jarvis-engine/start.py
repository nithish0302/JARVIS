import uvicorn
from jarvis_engine.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "jarvis_engine.main:app",
        host=settings.JARVIS_HOST,
        port=settings.JARVIS_PORT,
        reload=True
    )
