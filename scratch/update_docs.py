import re

def update_current_status():
    with open("docs/CURRENT_STATUS.md", "r", encoding="utf-8") as f:
        content = f.read()
        
    content = content.replace(
        "Current Milestone: Milestone 1 - Zustand Stores + Remove Mock Data",
        "Current Milestone: Milestone 2 - jarvis-engine FastAPI Server"
    )
    
    content = content.replace(
        """**Milestone 1 - Zustand Stores + Remove Mock Data**

Status: **Complete; awaiting review.**

The first milestone of Phase 2 is complete. The application now uses Zustand for global state. `useConversationStore`, `useAIStore`, `usePersonalityStore`, and `useAppStore` were created and integrated into `App.tsx` and `ChatView.tsx`, removing all mock data.

Validation passed: unit tests, lint, and the production build.""",
        """**Milestone 2 - jarvis-engine FastAPI Server**

Status: **Complete; awaiting review.**

The second milestone of Phase 2 is complete. The jarvis-engine FastAPI server foundation was built with provider abstraction layer and SQLite conversation storage.

Validation passed: API endpoints responded successfully."""
    )
    
    content = content.replace(
        "| Phase 2 - Milestone 1: Zustand Stores + Remove Mock Data                | Complete; awaiting review | Introduced useConversationStore, useAIStore, usePersonalityStore, useAppStore. Refactored App and ChatView to rely on global state.           |",
        "| Phase 2 - Milestone 1: Zustand Stores + Remove Mock Data                | Complete                  | Introduced useConversationStore, useAIStore, usePersonalityStore, useAppStore. Refactored App and ChatView to rely on global state.           |\n| Phase 2 - Milestone 2: jarvis-engine FastAPI Server                     | Complete; awaiting review | Built FastAPI server foundation, SQLite storage, and provider abstraction.                                                                    |"
    )
    
    content = content.replace(
        """## Pending milestone

**Phase 1 - Milestone 5 review**

Awaiting review. No further implementation milestone should begin until this
milestone is accepted.

## Next planned milestone

The next milestone for Phase 1 - Desktop UI will be Milestone 6, which continues to enrich the desktop user experience.""",
        """## Pending milestone

**Phase 2 - Milestone 2 review**

Awaiting review. No further implementation milestone should begin until this milestone is accepted.

## Next planned milestone

The next milestone for Phase 2 - AI Integration will be Milestone 3, which focuses on Ollama connection."""
    )
    
    with open("docs/CURRENT_STATUS.md", "w", encoding="utf-8") as f:
        f.write(content)

def append_development_log():
    entry = """
## Phase 2 - Milestone 2: jarvis-engine FastAPI Server

Date: 2026-08-08

Objective: Build the jarvis-engine FastAPI server 
foundation with provider abstraction layer and 
SQLite conversation storage.

Files created:
- services/jarvis-engine/src/jarvis_engine/core/
  config.py, database.py, models.py
- services/jarvis-engine/src/jarvis_engine/providers/
  base.py, manager.py, ollama.py, openrouter.py
- services/jarvis-engine/src/jarvis_engine/memory/
  conversation.py
- services/jarvis-engine/src/jarvis_engine/api/
  routes.py
- services/jarvis-engine/src/jarvis_engine/main.py
- services/jarvis-engine/start.py
- services/jarvis-engine/start.bat
- services/jarvis-engine/.env.example
- services/jarvis-engine/test_api.py

Validation:
- Server starts on http://localhost:8765
- GET /health returns status online, version 0.1.0,
  both providers listed (available: false — correct 
  for stubs)
- GET /providers returns both provider stubs
- POST /chat returns mock response
- SQLite database auto-created at data/jarvis.db
- CORS configured for Tauri port 1420

Status: Complete and approved.
"""
    with open("docs/DEVELOPMENT_LOG.md", "a", encoding="utf-8") as f:
        f.write(entry)

if __name__ == "__main__":
    update_current_status()
    append_development_log()
    print("Docs updated.")
