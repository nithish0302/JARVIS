# JARVIS Cleanup Report
**Generated:** 2026-08-20  
**Purpose:** Identify unused packages and files for potential removal

---

## Python Dependencies (pyproject.toml)

### ✅ Currently Used Packages

| Package | Usage | Files |
|---------|-------|-------|
| `aiosqlite` | Database operations | memory/conversation.py, core/database.py |
| `duckduckgo-search` | Web search | tools/web_search.py |
| `edge-tts` | Text-to-speech | voice/tts_engine.py |
| `fastapi` | Web framework | api/routes.py, main.py |
| `faster-whisper` | Speech-to-text | voice/voice_manager.py |
| `groq` | Groq AI provider | providers/groq_provider.py |
| `httpx` | HTTP client | providers/openrouter.py, providers/gemini_provider.py |
| `numpy` | Audio processing | voice/wake_word.py, voice/speech_recorder.py |
| `ollama` | Ollama provider | providers/ollama.py |
| `openwakeword` | Wake word detection | voice/wake_word.py |
| `pyaudio` | Audio input | voice/speech_recorder.py |
| `pydantic-settings` | Configuration | core/config.py |
| `pygame` | Audio playback | voice/tts_engine.py |
| `python-dotenv` | Environment variables | (implicit via pydantic-settings) |
| `sounddevice` | Audio streaming | voice/wake_word.py |
| `soundfile` | Audio file I/O | voice/voice_manager.py |
| `tavily-python` | Tavily search (fallback) | tools/web_search.py |
| `uvicorn` | ASGI server | Used to run the app |

### ⚠️ Potentially Unused Packages

| Package | Reason | Recommendation |
|---------|--------|----------------|
| `chromadb` | No imports found in codebase | **REMOVE** - not used anywhere |
| `sentence-transformers` | No imports found | **REMOVE** - embeddings not implemented |

### 📦 Packages with Minimal Usage

| Package | Current Usage | Notes |
|---------|---------------|-------|
| `tavily-python` | tools/web_search.py (fallback only) | Only used when TAVILY_API_KEY is set, DuckDuckGo is primary |

---

## Python Files Analysis

### Empty or Minimal __init__.py Files

These files exist but contain no code (or only minimal imports):

```
services/jarvis-engine/src/jarvis_engine/__init__.py
services/jarvis-engine/src/jarvis_engine/core/__init__.py
services/jarvis-engine/src/jarvis_engine/core/event_bus/__init__.py
services/jarvis-engine/src/jarvis_engine/core/planner/__init__.py
services/jarvis-engine/src/jarvis_engine/core/router/__init__.py
services/jarvis-engine/src/jarvis_engine/core/security/__init__.py
services/jarvis-engine/src/jarvis_engine/core/permissions/__init__.py
services/jarvis-engine/src/jarvis_engine/core/memory/__init__.py
services/jarvis-engine/src/jarvis_engine/core/logging/__init__.py
services/jarvis-engine/src/jarvis_engine/core/configuration/__init__.py
services/jarvis-engine/src/jarvis_engine/core/lifecycle/__init__.py
services/jarvis-engine/src/jarvis_engine/providers/__init__.py
services/jarvis-engine/src/jarvis_engine/memory/__init__.py
services/jarvis-engine/src/jarvis_engine/api/__init__.py
services/jarvis-engine/src/jarvis_engine/tools/__init__.py
services/jarvis-engine/src/jarvis_engine/voice/__init__.py
```

**Status:** These are Python package markers - keep them (required for imports to work)

### Unused Python Files

| File | Status | Recommendation |
|------|--------|----------------|
| `test_foreground.py` | Test file in src/ | **MOVE** to tests/ directory or remove |

### Unused Core Directories

These directories exist but contain no implementation:

```
core/event_bus/          - Empty (only __init__.py)
core/planner/            - Empty (only __init__.py)
core/router/             - Empty (only __init__.py)
core/security/           - Empty (only __init__.py)
core/permissions/        - Empty (only __init__.py)
core/memory/             - Empty (only __init__.py)
core/logging/            - Empty (only __init__.py)
core/configuration/      - Empty (only __init__.py)
core/lifecycle/          - Empty (only __init__.py)
```

**Recommendation:** These are placeholder directories for future features. Either:
- **REMOVE** if not planned for near-term use
- **KEEP** if part of architectural roadmap

---

## Frontend Dependencies (package.json)

### ✅ Currently Used Packages

| Package | Usage | Component Type |
|---------|-------|----------------|
| `@react-three/drei` | 3D helpers | Orb/AiCore 3D visualization |
| `@react-three/fiber` | React Three.js | Orb/AiCore 3D rendering |
| `@tauri-apps/api` | Tauri IPC | System integration |
| `@tauri-apps/plugin-shell` | Shell commands | Desktop automation |
| `clsx` | Conditional classes | All components |
| `framer-motion` | Animations | Orb, UI transitions |
| `lucide-react` | Icons | UI components |
| `react` | Core framework | All components |
| `react-dom` | React rendering | App entry |
| `react-markdown` | Markdown rendering | Message display |
| `three` | 3D engine | Orb visualization |
| `zustand` | State management | All stores |

### ✅ All Frontend Packages Are Used

**Result:** No unused frontend dependencies found. All packages are actively used in the codebase.

---

## Frontend Files Analysis

### Unused/Deprecated Files

| File | Status | Recommendation |
|------|--------|----------------|
| `ChatView.old.tsx` | Old implementation | **REMOVE** - superseded by ChatFullView |
| `ChatView.old.test.tsx` | Old test | **REMOVE** - no longer relevant |
| `AppShell.old.tsx` | Old layout | **REMOVE** - superseded by current layout |
| `AppHeader.old.tsx` | Old header | **REMOVE** - superseded by Topbar |

### Test Files Without Implementation

All `.test.tsx` files exist but many have no tests yet:
- `AiCore.test.tsx` - Empty/minimal
- `AiCoreIdle.test.tsx` - Empty/minimal
- `AiIdentity.test.tsx` - Empty/minimal
- (Many more...)

**Recommendation:** Either implement tests or remove test scaffolding files

---

## Summary & Recommendations

### High Priority Removals

1. **Python packages:**
   - `chromadb` - Not used (save ~200MB)
   - `sentence-transformers` - Not used (save ~500MB)

2. **Python files:**
   - `test_foreground.py` - Move to tests/ or remove

3. **Frontend files:**
   - `ChatView.old.tsx`
   - `ChatView.old.test.tsx`
   - `AppShell.old.tsx`
   - `AppHeader.old.tsx`

4. **Empty core directories:**
   - `core/event_bus/`
   - `core/planner/`
   - `core/router/`
   - `core/security/`
   - `core/permissions/`
   - `core/memory/` (duplicate of top-level memory/)
   - `core/logging/`
   - `core/configuration/`
   - `core/lifecycle/`

### Medium Priority

1. **Empty test files:** Implement or remove test scaffolding
2. **tavily-python:** Consider removing if DuckDuckGo is sufficient

### Estimated Savings

- **Disk space:** ~700MB (chromadb + sentence-transformers)
- **Install time:** ~30 seconds faster
- **Clarity:** Cleaner dependency list
- **Maintenance:** Less code to maintain

---

## Next Steps

**DO NOT REMOVE YET** - This is a report only.

1. Review recommendations with team
2. Test functionality after each removal
3. Update this report as changes are made
4. Re-run dependency analysis quarterly

---

**Note:** This report is based on static analysis. Some packages may have indirect usage not detected by grep. Always test thoroughly before removing dependencies.
