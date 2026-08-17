# JARVIS Master Status Document

> **Purpose:** Ground-truth reference for AI assistants and new contributors.
> All claims are verified against actual source code.
> Last audited: 2026-08-16.

---

## 1. What JARVIS Can Actually Do Right Now

### ✅ Streaming AI Chat
- Sends messages to `/chat/stream` which returns NDJSON chunks of type `meta`, `token`, and `done`
- The frontend reads the stream token-by-token and renders incrementally in real-time
- Full multi-provider fallback: if the primary provider fails mid-stream, the next is tried (only if no tokens have been yielded yet)
- Works in both **Graph Mode** (ChatShell overlay) and **Chat Mode** (ChatFullView full-screen)

### ✅ Non-Streaming Chat (Legacy)
- `/chat` endpoint also works: sends full message, waits, returns complete response
- Not used by the frontend currently (frontend exclusively calls `/chat/stream`)

### ✅ Multi-Provider AI (4 Providers, Priority Order)
1. **Gemini** (`gemini-2.5-flash`) — checks `GEMINI_API_KEY != ""`
2. **OpenRouter** (`google/gemma-4-27b-it:free`) — checks API key + does live HTTP probe to `openrouter.ai/api/v1/models`
3. **Groq** (`llama-3.3-70b-versatile`) — checks `GROQ_API_KEY != ""`
4. **Ollama** (`llama3.2:3b`) — checks local `http://localhost:11434/api/tags` returns 200

### ✅ Conversation Persistence
- Every message (user, assistant, system) is saved to SQLite via `aiosqlite`
- `conversation_id` (UUID) is stored in `localStorage` key `jarvis_conversation_id`
- On startup, `useConversationLoader` hook restores the last conversation from the engine
- `/conversations` endpoint returns last 10 conversations ordered by `updated_at DESC`

### ✅ Conversation Management (Full CRUD)
- **List**: `GET /conversations` → last 10, with title derived from DB or first user message
- **Load**: `GET /conversation/{id}` → full message history (system messages filtered out)
- **Delete**: `DELETE /conversation/{id}` → requires PIN `0523` in `PinAuthModal`
- **Rename**: `PUT /conversation/{id}/title` → enforces unique title constraint (case-insensitive)
- **New Chat button** in both ChatShell and ChatFullView clears local state and removes localStorage ID
- Conversation titles are unique — backend raises `ValueError` and returns HTTP 400 on collision

### ✅ Long-Term Memory System
- Extracts memories from user messages using keyword trigger matching (5 categories: preference, personal, project, goal, fact)
- Saves memories to `memories` table in SQLite with `importance` score (5–8) and `category`
- Deduplicates by first 100 chars of content (case-insensitive)
- At every chat turn, top 5 relevant memories are fetched with LIKE-based word search and injected into the system prompt
- Memory count displayed live in Topbar (refreshed every 60s)
- Full CRUD via API: `GET /memories`, `POST /memories`, `DELETE /memories/{id}`, `GET /memories/search?q=`, `POST /memories/deduplicate`

### ✅ Web Search (Background, Partial)
- `needs_web_search()` detects search intent via substring matching against 22 trigger phrases
- `extract_search_query()` strips up to 8 known prefixes to get a clean query
- **Tavily** is primary search provider (requires `TAVILY_API_KEY`); **DuckDuckGo** is automatic fallback
- **Critical known bug:** In `/chat/stream`, search runs as a background `asyncio.create_task` and the AI streams its response before search results arrive. The AI never sees search results for the current turn — only the next turn (saved as `role=system` message to DB)
- In `/chat` (non-streaming), `asyncio.gather` runs search and LLM simultaneously — same bug, LLM doesn't see results
- `SearchBadge` and `SourcesList` UI components exist and render in ChatFullView when `searchPerformed=true` and `sources` are non-empty

### ✅ [UI_ACTION] Protocol
- AI embeds `[UI_ACTION:command]` tags in its responses
- `uiActionParser.ts` extracts them with regex `/\[UI_ACTION:([^\]]+)\]/g` and strips from displayed text
- `uiActionExecutor.ts` translates actions to Zustand state mutations
- `ActionFeedback` component shows a 5-second floating message near the Orb
- `inspectorMessage` in `useAppStore` logs executed action to the Inspector panel (auto-clears in 3s)

### ✅ Live System Stats (via Tauri/Rust)
- `get_system_info` Tauri command called every 3 seconds from `LeftColumn`
- Returns: CPU usage %, CPU name, CPU core count, RAM used/total GB, RAM %
- GPU info is **hardcoded** in `lib.rs` as GTX 1650 + Intel UHD (not dynamically read from sysinfo)
- SSD info is also **hardcoded** (410/512 GB)

### ✅ Interactive Graph Canvas
- Custom Canvas 2D animation (no Three.js/WebGL despite packages being installed)
- 3 levels: Level 0 (collapsed), Level 1 (hubs expanded), Level 2 (hub drilled-down with leaves)
- 7 hub nodes: Skills, Tools, Files, Notes, Worlds, Models, Conversations
- Leaf data is **static hardcoded** for all hubs except Conversations, which loads from `GET /conversations`
- Clicking a conversation leaf loads that conversation's full history and switches to chat mode
- Graph animates continuously (rotation, hover slow-down effect)
- Click core → toggle Level 0/1; click hub → drill to Level 2; click "← BACK" or core → return to Level 1

### ✅ Settings UI
- Three sections: AI Provider, Appearance, About
- AI Provider: select provider, enter model name, enter API keys (saved to `.env` file via `python-dotenv`), test connection
- Provider switch sends `POST /provider/switch` which reorders `provider_manager.providers` list
- API keys submitted to `/config/{provider}-key` which writes to both `os.environ` and `.env` file at runtime

### ✅ Provider Switching at Runtime
- `POST /provider/switch` reorders the provider list in memory
- `UI_ACTION:switch_provider:name` fires from AI response → calls `jarvisApi.switchProvider()` → also updates `useAIStore.provider`

### ✅ ConversationPanel (Memory Index)
- Slide-in panel opened via Dock button or `conversations_open` UI action
- Lists last 10 conversations with title, time-ago, and UUID prefix
- Inline rename: click pencil icon → inline input → submit/blur saves via `PUT /conversation/{id}/title`
- Delete: click trash icon → `PinAuthModal` with 4-digit PIN `0523` → calls `DELETE /conversation/{id}`
- Clicking a conversation loads its full history into the chat store

### ✅ Engine Health Monitoring
- `useEngineStatus` hook polls `/health` every 30 seconds
- Sets `useAIStore.status` to `"idle"` or `"offline"` based on response
- First available provider name and model synced into store
- Memory count polled every 60 seconds separately

---

## 2. Tech Stack (from actual package files)

### Frontend — `apps/desktop/package.json`

| Package | Version |
|---|---|
| `react` | `^19.1.0` |
| `react-dom` | `^19.1.0` |
| `zustand` | `^5.0.14` |
| `framer-motion` | `^12.43.0` |
| `@tauri-apps/api` | `^2` |
| `@tauri-apps/plugin-shell` | `^2.3.5` |
| `clsx` | `^2.1.1` |
| `lucide-react` | `^1.28.0` |
| `three` | `^0.185.1` |
| `@react-three/fiber` | `^9.6.1` |
| `@react-three/drei` | `^10.7.7` |
| `tailwindcss` | `^4.3.3` |
| `vite` | `^7.0.4` |
| `typescript` | `~5.8.3` |
| `vitest` | `^4.1.10` |

> **Note:** `three`, `@react-three/fiber`, `@react-three/drei` are installed but **not used**. The graph uses Canvas 2D API directly.

### Backend — `services/jarvis-engine/pyproject.toml`

| Package | Version |
|---|---|
| `fastapi` | `>=0.141.1` |
| `uvicorn` | `>=0.52.1` |
| `aiosqlite` | `>=0.22.1` |
| `httpx` | `>=0.28.1` |
| `pydantic-settings` | `>=2.14.2` |
| `python-dotenv` | `>=1.2.2` |
| `groq` | `>=1.6.0` |
| `tavily-python` | `>=0.7.27` |
| `duckduckgo-search` | `>=8.1.1` |
| `ollama` | `>=0.6.2` |
| `chromadb` | `>=1.5.9` |
| `sentence-transformers` | `>=5.7.0` |
| Python required | `>=3.12` |

> **Note:** `chromadb` and `sentence-transformers` are installed but **not used** in any current code. These are dependencies for a planned vector memory system.

### Rust — `apps/desktop/src-tauri/src/lib.rs`

| Crate | Usage |
|---|---|
| `sysinfo` | CPU/RAM stats |
| `serde_json` | JSON serialization |
| `tauri` | Desktop shell, command invocation |
| `tauri-plugin-shell` | Opens URLs in browser (used by SourcesList) |

---

## 3. Complete Folder Structure

```
D:\JARVIS\
├── apps/
│   └── desktop/
│       ├── package.json
│       ├── src/
│       │   ├── App.tsx                          # Root component, view router
│       │   ├── main.tsx                         # React DOM entry point
│       │   ├── components/
│       │   │   ├── ai-core/                     # (legacy, unused)
│       │   │   ├── chat/
│       │   │   │   ├── ChatFullView/
│       │   │   │   │   └── ChatFullView.tsx      # Full-screen chat mode layout
│       │   │   │   ├── ChatShell/
│       │   │   │   │   └── ChatShell.tsx         # Floating chat input overlay (graph mode)
│       │   │   │   ├── SearchBadge/
│       │   │   │   │   └── SearchBadge.tsx       # "Searched: query" pill
│       │   │   │   └── SourcesList/
│       │   │   │       └── SourcesList.tsx        # Clickable source links
│       │   │   ├── conversations/
│       │   │   │   └── ConversationPanel/
│       │   │   │       ├── ConversationPanel.tsx  # Slide-in "Memory Index" panel
│       │   │   │       └── PinAuthModal.tsx       # 4-digit PIN confirmation modal
│       │   │   ├── graph/
│       │   │   │   └── GraphCanvas/
│       │   │   │       └── GraphCanvas.tsx        # Canvas 2D animated knowledge graph
│       │   │   ├── layout/
│       │   │   │   ├── Dock/
│       │   │   │   │   └── Dock.tsx              # Vertical icon sidebar (graph, history, settings, mic)
│       │   │   │   ├── LeftColumn/
│       │   │   │   │   └── LeftColumn.tsx         # Inspector + System Stats panel + Chat Mode toggle
│       │   │   │   ├── RightColumn/
│       │   │   │   │   └── RightColumn.tsx        # Filter legend + Orb + Graph stats
│       │   │   │   ├── Stage/
│       │   │   │   │   └── Stage.tsx             # Stage + Scene layout wrappers
│       │   │   │   ├── Topbar/
│       │   │   │   │   └── Topbar.tsx            # Brand + model/provider pill + memory count + status
│       │   │   │   └── LayoutProvider.tsx        # Thin wrapper (no logic currently)
│       │   │   ├── orb/
│       │   │   │   ├── Orb/
│       │   │   │   │   └── Orb.tsx              # Animated orb widget with status ring
│       │   │   │   └── ActionFeedback/
│       │   │   │       └── ActionFeedback.tsx    # Floating UI action feedback text
│       │   │   ├── settings/
│       │   │   │   ├── SettingsView/             # Settings page container
│       │   │   │   ├── AIProviderSection/        # Provider/model/key config UI
│       │   │   │   ├── AppearanceSection/        # (stub, no actual settings)
│       │   │   │   └── AboutSection/             # Version info
│       │   │   └── ui/                           # Primitive components
│       │   │       ├── Button/, Card/, Input/, Select/
│       │   │       ├── Checkbox/, Switch/, Spinner/
│       │   │       └── ...
│       │   ├── hooks/
│       │   │   ├── useJarvisChat.ts             # Core chat hook (send, stream, actions)
│       │   │   ├── useEngineStatus.ts           # Polls /health every 30s
│       │   │   └── useConversationLoader.ts     # Restores conversation from localStorage on startup
│       │   ├── services/
│       │   │   └── jarvisApi.ts                 # All HTTP calls to jarvis-engine (port 8765)
│       │   ├── stores/
│       │   │   ├── useAppStore.ts               # UI layout state
│       │   │   ├── useConversationStore.ts      # Messages, streaming, conversation ID/title
│       │   │   ├── useAIStore.ts               # Provider, model, status, memory count
│       │   │   └── usePersonalityStore.ts       # Personality settings (not yet wired to backend)
│       │   ├── types/
│       │   │   └── chat.types.ts               # Message, SearchSource interfaces
│       │   └── utils/
│       │       ├── uiActionParser.ts            # Regex parser for [UI_ACTION:...] tags
│       │       └── uiActionExecutor.ts          # Translates actions to Zustand mutations
│       └── src-tauri/
│           └── src/
│               └── lib.rs                       # Rust: get_system_info command
├── docs/
│   ├── CURRENT_STATUS.md
│   ├── DEVELOPMENT_LOG.md
│   ├── JARVIS_MASTER_STATUS.md                  # This file
│   └── architecture/
│       ├── PROJECT.md
│       ├── ROADMAP.md
│       ├── ARCHITECTURE.md
│       ├── DESIGN_SYSTEM.md
│       └── DESIGN_TOKENS.md
└── services/
    └── jarvis-engine/
        ├── start.py                             # Entry: uvicorn on localhost:8765 with reload
        ├── .env.example
        ├── pyproject.toml
        └── src/jarvis_engine/
            ├── main.py                          # FastAPI app, CORS (localhost:1420), lifespan DB init
            ├── api/
            │   └── routes.py                    # All API endpoints (612 lines)
            ├── core/
            │   ├── config.py                    # Settings via pydantic-settings + .env
            │   ├── database.py                  # SQLite schema init (3 tables)
            │   └── models.py                    # Pydantic models (Message, ChatRequest, etc.)
            ├── memory/
            │   ├── conversation.py              # Conversation CRUD + title uniqueness
            │   └── memory_manager.py            # Memory save/search/extract/deduplicate
            ├── providers/
            │   ├── base.py                      # Abstract BaseProvider
            │   ├── manager.py                   # ProviderManager with priority list
            │   ├── gemini_provider.py            # Gemini via REST API (httpx)
            │   ├── groq_provider.py              # Groq via SDK (synchronous in async wrapper)
            │   ├── openrouter.py                # OpenRouter via REST API (httpx)
            │   └── ollama.py                    # Ollama via REST API (httpx)
            └── tools/
                ├── search_detector.py           # needs_web_search(), extract_search_query()
                └── web_search.py               # search_tavily(), search_duckduckgo(), format_search_results()
```

---

## 4. AI Providers (Actual Implementation)

### Provider Priority Order (`manager.py`)
1. GeminiProvider
2. OpenRouterProvider
3. GroqProvider
4. OllamaProvider

The first provider for which `is_available()` returns `True` is used.

---

### GeminiProvider (`gemini_provider.py`)
- **Model:** `settings.GEMINI_MODEL` (default: `gemini-2.5-flash`)
- **`is_available()`:** Returns `True` if `settings.GEMINI_API_KEY != ""`  (no live probe)
- **`chat()`:** `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` via `httpx.AsyncClient`, timeout 60s. System messages sent as `system_instruction`.
- **`stream()`:** `POST .../streamGenerateContent?alt=sse`, parses SSE lines, yields text tokens

---

### OpenRouterProvider (`openrouter.py`)
- **Model:** `settings.OPENROUTER_MODEL` (default: `google/gemma-4-27b-it:free`)
- **`is_available()`:** Requires API key AND does live `GET https://openrouter.ai/api/v1/models` HTTP probe with 5s timeout
- **`chat()`:** `POST https://openrouter.ai/api/v1/chat/completions`, OpenAI-compatible format, timeout 60s
- **`stream()`:** Same endpoint with `"stream": true`, parses SSE `data:` lines

---

### GroqProvider (`groq_provider.py`)
- **Model:** `settings.GROQ_MODEL` (default: `llama-3.3-70b-versatile`)
- **`is_available()`:** Returns `bool(settings.GROQ_API_KEY)` (no live probe)
- **`chat()`:** Uses `groq.Groq` SDK synchronously inside `async def` — **BLOCKS event loop**
- **`stream()`:** Uses `groq.Groq` SDK `stream=True` synchronously inside `async def` — **BLOCKS event loop**, yields chunks via `for chunk in response`

---

### OllamaProvider (`ollama.py`)
- **Model:** `settings.OLLAMA_MODEL` (default: `llama3.2:3b`)
- **`is_available()`:** Live probe to `http://localhost:11434/api/tags` with 3s timeout
- **`chat()`:** `POST http://localhost:11434/api/chat`, httpx async, `stream: false`
- **`stream()`:** `POST` same URL, `stream: true`, parses JSON lines, yields `message.content`

---

## 5. API Endpoints (from routes.py)

| Method | Path | Description | Request | Response |
|---|---|---|---|---|
| `POST` | `/chat` | Non-streaming chat | `{message, conversation_id?, provider, model}` | `{response, conversation_id, provider_used, model_used, search_performed, search_query, sources[]}` |
| `POST` | `/chat/stream` | Streaming chat (NDJSON) | Same as above | `meta\|token\|done\|error` chunks |
| `POST` | `/search` | Direct web search | `{query: str}` | `{query, results[], formatted}` |
| `GET` | `/health` | Engine health + provider status | — | `{status, version, providers[]}` |
| `GET` | `/conversations` | Last 10 conversations | — | `[{id, title, created_at, updated_at, message_count}]` |
| `GET` | `/conversation/{id}` | Full message history | — | `[{role, content, timestamp}]` (system filtered) |
| `DELETE` | `/conversation/{id}` | Delete conversation | — | `{status, conversation_id}` |
| `PUT` | `/conversation/{id}/title` | Rename (unique enforced) | `{title: str}` | `{status, conversation_id, title}` or HTTP 400 |
| `GET` | `/providers` | All provider statuses | — | `[{name, available, model}]` |
| `POST` | `/provider/switch` | Switch active provider | `{provider: str, model: str}` | `{status, provider, model}` |
| `GET` | `/memories` | All memories (max 50) | — | `[Memory]` |
| `POST` | `/memories` | Create memory | `{content, category?, importance?}` | `Memory` |
| `DELETE` | `/memories/{id}` | Delete memory | — | `{deleted: bool}` |
| `GET` | `/memories/search` | Search memories | `?q=query` | `[Memory]` |
| `POST` | `/memories/deduplicate` | Remove duplicate memories | — | `{status, memories_remaining}` |
| `POST` | `/config/openrouter-key` | Set OpenRouter key at runtime | `{api_key: str}` | `{status}` |
| `POST` | `/config/groq-key` | Set Groq key at runtime | `{api_key: str}` | `{status}` |
| `POST` | `/config/gemini-key` | Set Gemini key at runtime | `{api_key: str}` | `{status}` |

### Stream chunk format (`/chat/stream`)

```json
// First chunk
{"type": "meta", "conversation_id": "uuid", "search_performed": true, "search_query": "query", "sources": []}

// Per token
{"type": "token", "content": "hello"}

// Final chunk
{"type": "done", "conversation_id": "uuid", "full_response": "...", "sources": [{title, url, snippet, source}]}

// On error
{"type": "error", "message": "..."}
```

---

## 6. Database Schema (from database.py)

**File:** `services/jarvis-engine/data/jarvis.db` (SQLite)

### Table: `conversations`
| Column | Type | Notes |
|---|---|---|
| `id` | `TEXT PRIMARY KEY` | UUID |
| `title` | `TEXT` | Default `"New Conversation"`; falls back to first message content in queries |
| `created_at` | `TEXT` | ISO 8601 |
| `updated_at` | `TEXT` | ISO 8601, updated on every new message |

### Table: `messages`
| Column | Type | Notes |
|---|---|---|
| `id` | `TEXT PRIMARY KEY` | UUID |
| `conversation_id` | `TEXT` | FK → conversations.id |
| `role` | `TEXT` | `"user"`, `"assistant"`, or `"system"` |
| `content` | `TEXT` | Full message text |
| `timestamp` | `TEXT` | ISO 8601 |
| `provider_used` | `TEXT` | e.g. `"gemini"` |
| `model_used` | `TEXT` | e.g. `"gemini-2.5-flash"` |

### Table: `memories`
| Column | Type | Notes |
|---|---|---|
| `id` | `TEXT PRIMARY KEY` | UUID |
| `content` | `TEXT NOT NULL` | Prefixed with `"Nithish said: "` |
| `category` | `TEXT DEFAULT 'general'` | `preference`, `personal`, `project`, `goal`, `fact`, `general` |
| `importance` | `INTEGER DEFAULT 5` | Range 5–8 |
| `created_at` | `TEXT NOT NULL` | ISO 8601 UTC |
| `last_accessed` | `TEXT NOT NULL` | ISO 8601 UTC, updated on retrieval |
| `access_count` | `INTEGER DEFAULT 0` | Incremented on retrieval |
| `source_conversation_id` | `TEXT` | UUID of originating conversation |

---

## 7. Memory System (Actual Implementation)

### Memory Extraction (`memory_manager.py:extract_and_save_memories`)

Triggered **after every chat turn** from the `assistant` response save step in both `/chat` and `/chat/stream`.

**Algorithm:**
1. Skip messages under 10 chars
2. Scan `msg_lower` for trigger phrases using simple `in` substring matching
3. First match across 5 ordered category lists wins:
   - **personal** (importance 8): `"my name is"`, `"i am "`, `"i'm "`, `"i work"`, `"i live"`, `"i study"`, `"i'm from"`, `"call me"`, `"you can call me"`
   - **project** (importance 7): `"i'm building"`, `"i'm working on"`, `"i'm developing"`, `"my project"`, `"we're building"`, `"i'm creating"`, `"i'm making"`, `"my app"`, `"my system"`
   - **preference** (importance 6): `"i prefer"`, `"i like"`, `"i love"`, `"i enjoy"`, `"i hate"`, `"i don't like"`, `"i dislike"`, `"i always"`, `"i usually"`, `"i never"`, `"my favorite"`, `"i find it"`, `"i think"`
   - **goal** (importance 6): `"i want to"`, `"i need to"`, `"my goal"`, `"i'm trying to"`, `"i plan to"`, `"i hope to"`, `"i wish"`
   - **fact** (importance 5): `"i have"`, `"my pc"`, `"my computer"`, `"my laptop"`, `"my setup"`, `"i use"`, `"i'm using"`, `"i run"`, `"i installed"`
4. Content saved as first 200 chars, prefixed `"Nithish said: "`
5. Duplicate check: compares first 100 chars (lowercase) against existing memories; if match found, updates `last_accessed` instead of inserting

### Memory Retrieval (`get_relevant_memories`)
1. Splits query into words > 3 chars
2. Builds SQL `WHERE LOWER(content) LIKE '%word%' OR ...` for all words
3. Orders by `importance DESC, last_accessed DESC`, limit 5
4. Updates `last_accessed` and `access_count` for retrieved memories
5. Injected into every prompt as `"\n\nRelevant memories about Nithish:\n- {content}"`

---

## 8. Search System (Actual Implementation)

### Detection (`search_detector.py:needs_web_search`)

```python
SEARCH_TRIGGERS = [
  "search for", "look up", "find information",
  "what is the latest", "current price",
  "today", "right now", "recent", "news about",
  "who is", "when did", "what happened",
  "how much does", "where is", "what time",
  "weather in", "stock price", "score of",
  "search the web", "search online",
  "google", "find out", "tell me about",
]

UI_EXCLUSIONS = [
  "show my", "open ", "close ", "collapse",
  "expand", "switch to", "go to", "chat mode",
  "graph mode", "show conversations",
  "show skills", "show tools", "show files",
]
```

Logic:
1. If any `UI_EXCLUSIONS` substring in message → return `False`
2. If message < 8 chars → return `False`
3. If any `SEARCH_TRIGGERS` substring in message → return `True`
4. 5 additional `question_starters` checked with `startswith()`: `"what is the current"`, `"what are the latest"`, `"who won"`, `"who is the"`, `"when is the next"`
5. Otherwise → return `False`

### Query Extraction (`extract_search_query`)
Strips up to 8 known prefixes using `startswith()` on the lowercased message:
`"search for "`, `"look up "`, `"search the web for "`, `"search online for "`, `"google "`, `"find "`, `"what is the latest "`, `"tell me about "`

If no prefix matches, returns the raw message unchanged (which happens for ~77% of detected search triggers).

### Tavily Search (`web_search.py:search_tavily`)
- Creates `TavilyClient(api_key=...)` and calls `client.search(query, max_results=4, search_depth="basic")`
- **This is a synchronous blocking call inside an `async def` — blocks the event loop**
- Returns list of `{title, url, snippet (≤300 chars), source (domain only)}`

### DuckDuckGo Fallback (`search_duckduckgo`)
- Used when Tavily key missing or Tavily returns empty
- `DDGS().text(query, max_results=5)` — also synchronous blocking in async wrapper
- Returns same dict format

### Search Context Storage
What gets saved to DB (role=`"system"`):
```
[Search results for: {query}]
- {title} ({domain})
- {title} ({domain})
- {title} ({domain})
```
Only titles and domains — **no snippets**. Retrieved on next turn as `search_context_accumulated` and appended to system prompt.

---

## 9. [UI_ACTION] Protocol

### Supported Actions (exact strings)

| Tag | Effect in `uiActionExecutor.ts` |
|---|---|
| `[UI_ACTION:chat_mode_on]` | `setChatMode(true)` |
| `[UI_ACTION:chat_mode_off]` | `setChatMode(false)` |
| `[UI_ACTION:graph_expand]` | `setChatMode(false)`, `setGraphLevel(1)` |
| `[UI_ACTION:graph_collapse]` | `setChatMode(false)`, `setGraphLevel(0)` |
| `[UI_ACTION:graph_open_hub:Skills]` | `setChatMode(false)`, `setActiveHub("Skills")`, `setGraphLevel(2)` |
| `[UI_ACTION:graph_open_hub:Tools]` | Same with "Tools" |
| `[UI_ACTION:graph_open_hub:Files]` | Same with "Files" |
| `[UI_ACTION:graph_open_hub:Notes]` | Same with "Notes" |
| `[UI_ACTION:graph_open_hub:Models]` | Same with "Models" |
| `[UI_ACTION:graph_open_hub:Conversations]` | Same + `setConversationPanelOpen(true)` |
| `[UI_ACTION:conversations_open]` | Opens panel + drills to Conversations hub |
| `[UI_ACTION:conversations_close]` | `setConversationPanelOpen(false)` |
| `[UI_ACTION:new_chat]` | `clearConversation()`, `setChatMode(true)` |
| `[UI_ACTION:new_chat:Title]` | `clearConversation()`, creates new UUID, calls `updateConversationTitle()`, `setChatMode(true)` |
| `[UI_ACTION:rename_chat:Title]` | `updateConversationTitle(currentId, title)`, updates `currentConversationTitle` |
| `[UI_ACTION:delete_conversation:Title]` | Finds conversation by title substring, sets `deletingConversationId` (triggers PinAuthModal) |
| `[UI_ACTION:open_chat:Title]` | Finds conversation by title substring, loads full history, `setChatMode(true)` |
| `[UI_ACTION:switch_provider:name]` | Updates `useAIStore.provider`, calls `POST /provider/switch` |

### Parser (`uiActionParser.ts`)
```typescript
const ACTION_REGEX = /\[UI_ACTION:([^\]]+)\]/g
```
- Extracts `type` and optional `payload` (split at first `:`)
- Strips all action tags from displayed text
- Also stripped from streaming content in `appendStreamToken` in `useConversationStore`

### Feedback System
After every executed action:
- `showActionFeedback(message)` → sets `actionFeedback` string, visible for 5s → rendered by `ActionFeedback` component near Orb
- `setInspectorMessage(msg)` → shows in Left column Inspector panel, auto-clears in 3s

---

## 10. Zustand Stores (Actual State Shape)

### `useAppStore`

```typescript
{
  view: "chat" | "settings"           // Current view (chat or settings page)
  graphOpen: boolean                  // Initial: true
  graphFocused: boolean               // Initial: true
  activeHub: string | null            // Which hub is drilled into
  conversationPanelOpen: boolean      // Initial: false
  chatMode: boolean                   // Initial: false (HUD mode)
  graphLevel: 0 | 1 | 2              // Initial: 1
  actionFeedback: string              // UI action feedback text
  actionFeedbackVisible: boolean      // Show/hide feedback
  inspectorMessage: string            // Inspector panel message
  deletingConversationId: string | null  // Triggers PinAuthModal
}
```

### `useConversationStore`

```typescript
{
  messages: Message[]                    // All chat messages in current session
  currentConversationId: string | null   // Persisted to localStorage
  isTyping: boolean
  streamingMessageId: string | null      // ID of in-progress streaming message
  streamingContent: string               // Accumulated tokens (UI_ACTION tags stripped live)
  streamingSearchQuery: string | null    // Search query shown during streaming
  currentConversationTitle: string | null // Displayed in ChatFullView header
}
```

### `useAIStore`

```typescript
{
  provider: "ollama" | "openrouter" | "groq" | "gemini"  // Initial: "ollama"
  model: string                          // Initial: "llama3.2:3b"
  status: "idle" | "connecting" | "streaming" | "error" | "offline"
  isStreaming: boolean
  error: string | null
  memoryCount: number                    // Refreshed from /memories every 60s
  openrouterKey: string
  groqKey: string
  geminiKey: string
}
```

### `usePersonalityStore`

```typescript
{
  mode: "assistant" | "developer" | "focus" | "executive" | "learning" | "automation"
  address: "sir" | "Nithish" | "boss"
  formality: number        // 0-100, initial 60
  verbosity: number        // 0-100, initial 50
  humor: number            // 0-100, initial 40
  proactivity: number      // 0-100, initial 50
}
```
> **Note:** `usePersonalityStore` is defined and its values are initialized but **never read by the backend**. The personality dials have no effect on AI behavior.

---

## 11. UI Layout (Actual Components)

### Root Layout (`App.tsx`)
```
<LayoutProvider>              ← Thin div wrapper
  <AnimatePresence>           ← Framer Motion view transitions
    IF view === "chat":
      <Stage>                 ← Full-screen div (.stage CSS)
        <Topbar />            ← Fixed top bar
        IF chatMode:
          <Scene className="chat-mode">
            <LeftColumn />    ← Inspector + System stats + Chat Mode toggle
            <ChatFullView />  ← Full-screen chat interface
            <RightColumn />   ← Filter + Orb + Graph stats
          </Scene>
        ELSE:
          <Scene>
            <LeftColumn />
            <GraphCanvas />   ← Canvas 2D graph animation
            <RightColumn />
          </Scene>
          <ChatShell />       ← Floating chat input at bottom
      </Stage>
      <Dock />                ← Vertical icon bar (left side)
      <ConversationPanel />   ← Slide-in panel (z-indexed overlay)
    ELSE (view === "settings"):
      <SettingsView />
      <Dock />                ← Absolute positioned top-right
```

### Topbar
- Brand logo: `J.A.R.V.I.S` with animated dot
- Three pills: `{model} · {provider}` | `{memoryCount} MEMORIES` | status label (`IDLE`/`THINKING...`/`ERROR`/`OFFLINE`)

### LeftColumn
- **Inspector panel**: Shows active hub info or `inspectorMessage` from UI actions
- **System panel**: Live CPU %, RAM GB, GPU bars (GPU is hardcoded, CPU/RAM are real)
- **Chat Mode toggle button** at bottom

### RightColumn
- **Filter panel**: Colored legend dots for all 7 hub types
- **Orb widget**: Animated rings, `J.A.R.V.I.S.` text, IDLE/SPEAKING/LISTENING status, `ActionFeedback`, model · provider caption
- **Graph stats panel**: Node count and link count (static from hub definitions)

### GraphCanvas
- HTML `<canvas>` element, Canvas 2D rendering
- Continuous `requestAnimationFrame` animation loop
- 3 levels of zoom/focus; 7 hub nodes; leaf nodes per hub

### ChatFullView (Chat Mode)
- Header row: conversation title (from `currentConversationTitle` or first message), "New Chat" button
- Scrollable message list with `SearchBadge` + message bubble + `SourcesList` per assistant message
- Input bar at bottom with send button, autofocus

### ChatShell (Graph Mode)
- Absolute positioned `w-[min(680px,88%)]` pill at `bottom-16px`
- Text input + "New" clear button + send button
- Shows streaming messages in a message log above (not separately scrollable)

---

## 12. Graph System (Actual Implementation)

### Levels
| Level | `graphOpen` | `activeHub` | What renders |
|---|---|---|---|
| 0 | `false` | `null` | Hub nodes collapsed tight around center |
| 1 | `true` | `null` | Hub nodes spread at 70% canvas radius |
| 2 | `true` | `"skills"` etc | Hubs spread + selected hub centered + leaves orbiting |

### Hub Nodes (hardcoded in `GraphCanvas.tsx` and `RightColumn.tsx`)
| Key | Label | Color | Leaf Count |
|---|---|---|---|
| `skills` | Skills | `#5aa9e6` | 6 (Python, React, TypeScript, Rust, FastAPI, Tauri) |
| `tools` | Tools | `#e85aa0` | 6 (Web Search, Memory, File System, Terminal, Browser, Calculator) |
| `files` | Files | `#7a8c93` | 6 (Documents, Downloads, Projects, Desktop, Pictures, Music) |
| `notes` | Notes | `#52d68a` | 5 (JARVIS Notes, Ideas, Tasks, Meeting Notes, Code Snippets) |
| `worlds` | Worlds | `#e8934b` | 4 (Home, Work, Projects, Archive) |
| `models` | Models | `#b98be8` | 6 (gemini-2.5-flash, llama3.2:3b, qwen2.5-coder:3b, OpenRouter, Groq, nomic-embed-text) |
| `conversations` | Conversations | `#ffb454` | Dynamic — loaded from `GET /conversations` (max 8) |

### UI Action → Graph Sync
`graph_open_hub:X` in `uiActionExecutor.ts`:
1. If at Level 0 or chatMode: set Level 1, wait 800ms, then `setActiveHub(X)` and Level 2
2. If already at Level 1: immediately `setActiveHub(X)` and Level 2

`GraphCanvas.tsx` has a `useEffect` watching `activeHub`:
- Finds the matching hub node in `hubNodesRef.current`
- Sets `stateRef.current.selectedHub` to trigger drill-down animation

### Drill-down Click (Conversations hub only)
Clicking a conversation leaf node:
1. Extracts `conversationId` from `leaf.id` (format: `"conversations-leaf-{id}"`)
2. Calls `getConversation(convoId)` via dynamic import
3. Clears store, loads messages, sets `graphOpen(false)`, `setChatMode(true)`

---

## 13. Known Issues (From Code Analysis)

### 🔴 Critical

1. **Search results never reach the AI for the current turn** — In `/chat/stream` (line 319), `asyncio.create_task` fires search in the background. The AI streams its full response before search results arrive. Results are saved to DB for the *next* turn only. In `/chat` (line 194), `asyncio.gather` runs search and LLM concurrently, but `full_messages` is already built before gather — LLM response is generated without search context.

2. **Groq SDK blocks the event loop** — `groq_provider.py` uses the synchronous `Groq` SDK inside `async def`. The entire FastAPI event loop freezes for the duration of every Groq API call (typically 1–3 seconds). Same issue in `search_tavily()` and `search_duckduckgo()` — synchronous HTTP calls inside `async def`.

### 🟡 Significant

3. **GPU stats are hardcoded** — `lib.rs` always returns `GTX 1650` and `Intel UHD` with `usage: 0`. These values never change regardless of actual hardware.

4. **SSD stats are hardcoded** — `lib.rs` always returns `410/512 GB` static values.

5. **`usePersonalityStore` is never used by the backend** — The personality mode, address, and dial values stored in Zustand have no effect on the JARVIS system prompt or AI behavior.

6. **`chromadb` and `sentence-transformers` installed but unused** — These packages add significant install time and disk usage but no code references them. They were likely installed for a planned vector memory system.

7. **Three.js packages installed but unused** — `three`, `@react-three/fiber`, `@react-three/drei` are in `package.json` but not imported anywhere. The graph uses Canvas 2D.

8. **Search context grows unboundedly** — `search_context_accumulated` (lines 280-281 in routes.py) concatenates ALL past `system` role messages from the conversation, including every previous search result. Long conversations will eventually bloat the system prompt.

9. **`format_search_results()` is dead code** — Defined in `web_search.py:83-97` with full snippet formatting, but never called. Routes.py builds its own minimal format (title + domain only) inline.

10. **`SearchResult` class defined twice** — Once in `web_search.py:5-9` (not a dataclass, just attribute annotations) and again as a Pydantic model in `models.py:49-53`. The one in `web_search.py` is never used.

11. **`from urllib.parse import urlparse` inside loop** — In `web_search.py`, this import runs on every search result (lines 26, 53). Should be a top-level import.

12. **Conversation panel shows `.id.split("-")[0]`** — ConversationPanel shows the first segment of the UUID as an ID badge, which is meaningless to users.

13. **PIN `0523` is hardcoded in frontend** — `ConversationPanel.tsx` line 109 checks `pin === "0523"` directly. Not configurable.

14. **`useConversationLoader` missing `setConversationTitle` in dependency array** — Line 97 lists `[status, messages.length, addMessage, setConversationId]` but uses `setConversationTitle` inside the effect without including it.

15. **Title shown in ChatFullView falls back to first user message** — `getTitle()` in `ChatFullView.tsx` uses `currentConversationTitle` first, then falls back to `messages[0].content`. But after `useConversationLoader` runs, it fetches the title asynchronously — there's a brief flash of the first message content.

---

## 14. What Is NOT Implemented Yet

Based on `ROADMAP.md` vs actual code:

| Feature | Status |
|---|---|
| Voice / Speech-to-Text | Not started. Dock has a mic button (`useState(false)`) with no functionality |
| Text-to-Speech / TTS | Not started |
| Wake word detection | Not started |
| Desktop automation (open apps, files, browser) | Not started |
| Vision / camera / screenshot analysis | Not started |
| Plugin system | Not started |
| Android app | Not started |
| Vector/semantic memory (ChromaDB) | Packages installed, zero code written |
| Personality system wired to backend | Store defined, not connected to prompts |
| Graph leaf data dynamic (non-conversations) | Skills/Tools/Files/Notes/Models are static hardcoded arrays |
| Web dashboard | Not started |

---

## 15. Environment Configuration

### `.env` file location
`services/jarvis-engine/.env` (copy from `.env.example`)

### Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `JARVIS_HOST` | `localhost` | No | Engine bind host |
| `JARVIS_PORT` | `8765` | No | Engine port (frontend hardcodes 8765) |
| `OLLAMA_HOST` | `http://localhost:11434` | No | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.2:3b` | No | Default Ollama model |
| `OPENROUTER_API_KEY` | `""` | If using OpenRouter | OpenRouter API key |
| `OPENROUTER_MODEL` | `google/gemma-4-27b-it:free` | No | OpenRouter model ID |
| `GROQ_API_KEY` | `""` | If using Groq | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | No | Groq model ID |
| `GEMINI_API_KEY` | `""` | If using Gemini | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | No | Gemini model ID |
| `TAVILY_API_KEY` | `""` | For web search | Tavily search API key |
| `SEARCH_PROVIDER` | `tavily` | No | `"tavily"` or falls back to DuckDuckGo |
| `DB_PATH` | `data/jarvis.db` | No | SQLite database path |
| `VERSION` | `0.1.0` | No | Shown in `/health` response |

### How to Start the Project

**Backend (required first):**
```bash
cd D:\JARVIS\services\jarvis-engine
uv run python start.py
# Engine starts on http://localhost:8765
# SQLite DB auto-created at data/jarvis.db
```

**Frontend (Tauri desktop):**
```bash
cd D:\JARVIS\apps\desktop
pnpm tauri dev
# Or just frontend (browser mode):
pnpm dev
# Opens on http://localhost:1420
```

**CORS note:** Backend allows `http://localhost:1420` only. Browser dev mode works; Tauri dev mode works. Production Tauri build needs different CORS config.

### How to Run Tests

**Backend:**
```bash
cd D:\JARVIS\services\jarvis-engine
uv run pytest
```

**Frontend:**
```bash
cd D:\JARVIS\apps\desktop
pnpm test        # Watch mode
pnpm test:run    # Single run
```

**Existing test:** `apps/desktop/src/utils/uiActionParser.test.ts` — tests the `parseUIActions` function.
