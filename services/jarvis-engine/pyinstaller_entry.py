"""Sidecar entry point for the PyInstaller-frozen backend.

Distinct from start.py: uvicorn's reload=True spawns a second watcher
subprocess that re-imports the app module from source - meaningless (and
broken, no source tree exists) inside a frozen exe, so it's off here.
Tauri's sidecar spawn/kill lifecycle is the process supervisor now; the
dev-mode file watcher isn't needed once this is the thing actually running.
"""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()

    import uvicorn
    from jarvis_engine.core.config import settings
    # Import the ASGI app object directly rather than uvicorn's usual
    # "module:attr" string form. That string is resolved by uvicorn's own
    # importlib call at runtime - invisible to PyInstaller's static
    # analysis, so jarvis_engine.main never made it into the frozen build
    # ("Could not import module jarvis_engine.main"). A real `import`
    # statement here is what PyInstaller actually traces.
    from jarvis_engine.main import app

    uvicorn.run(
        app,
        host=settings.JARVIS_HOST,
        port=settings.JARVIS_PORT,
        reload=False,
    )
