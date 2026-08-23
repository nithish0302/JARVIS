# JARVIS Phase 0-5 Architecture Audit

**Purpose**: Ground-truth audit of the current codebase (not the docs) to plan Phase 6+ (Personality System, Memory Upgrade, Plugin System, Dynamic UI Widgets, Skill Learning/Capability Registry). Every claim below was verified by reading the actual source, not by trusting `CLAUDE.md`, `docs/JARVIS_MASTER_STATUS.md`, `docs/CURRENT_STATUS.md`, or `docs/DEVELOPMENT_LOG.md`. Drift between those docs and reality is catalogued in Section 3.

Audited: 2026-08-21. Repo root: `D:\JARVIS`.

---

## 1. FRONTEND ARCHITECTURE (apps/desktop/)

### 1.1 Composition root and what's actually live

`apps/desktop/src/App.tsx` (lines 41-72) is the only place components get wired together:

- `view === "chat"` → `Stage` > `Topbar` + (`chatMode` ? `Scene.chat-mode`[`LeftColumn`, `ChatFullView`, `RightColumn`] : `Scene`[`LeftColumn`, `GraphCanvas`, `RightColumn`] + `ChatShell`) + `Dock` + `ConversationPanel`
- `view === "settings"` → `SettingsView` + `Dock`

That's the entire live component graph. A large fraction of `src/components/` is **not reachable from `App.tsx` at all** — dead/orphaned scaffolding from an apparent abandoned refactor:

**Confirmed dead (zero imports outside own file/tests):**
- Entire `ai-core/` tree: `AiCore`, `AiCoreIdle`, `AiIdentity`, `IdleView`, `SuggestionCard`, `SuggestionGrid`, `WelcomeMessage` — grep across all `.tsx` finds only intra-folder references.
- Entire secondary chat system: `chat/ConversationArea`, `chat/MessageList`, `chat/StreamingMessage`, `chat/ChatComposer`, `chat/ComposerToolbar`, `chat/SendButton`, `chat/MessageAvatar`, `chat/MessageBubble`, `chat/TypingIndicator` — all have `README.md` + `.test.tsx` but are never imported by `App.tsx`, `ChatShell`, or `ChatFullView`, which each build their own message list inline instead.
- `chat/ChatView/ChatView.old.tsx` (only imported by its own `.old.test.tsx`).
- `layout/AppHeader.old.tsx`, `layout/AppShell.old.tsx` (`AppShell.old` imports `AppHeader.old`; nothing imports `AppShell.old`).
- `layout/AppMain.tsx`, `layout/OverlayLayer.tsx`, `layout/StatusBar.tsx` — generic wrappers, zero external imports found.
- `stores/usePersonalityStore.ts` — fully unused; the app's real personality-mode UI runs on `useAIStore.personalityMode`/`modifier` instead (see 1.2).

**Live component notes** (each read in full):
- `components/orb/Orb/Orb.tsx` — hand-rolled Canvas2D HUD ring (lines 8-534), reads `status`/`voiceStatus`/`provider`/`model` from `useAIStore` and `graphMode` from `useAppStore`; branches render loop between 60fps rAF (3D mode) and a 1fps/draw-once static path (2D mode) for power saving (lines 466-486). Renders `ActionFeedback` + status caption + `{model} · {provider}`. Used only by `RightColumn`.
- `chat/ChatShell/ChatShell.tsx` — the floating chat input used in graph/HUD mode; self-contained, uses `useJarvisChat()` + `useConversationStore` + `useAppStore.graphFocused` for positioning; renders `ConfirmationButtons`.
- `chat/ChatFullView/ChatFullView.tsx` — the full "Chat Mode" panel; also self-contained, renders markdown via `ReactMarkdown`, `SearchBadge`/`SourcesList` per assistant message, its own input/send bar.
- `layout/LeftColumn/LeftColumn.tsx` — polls Tauri `invoke("get_system_info")` every 3s and `get_battery_info`/`get_disk_info` every 60s (guarded by `'__TAURI_INTERNALS__' in window`); renders an "Inspector" panel + CPU/RAM/GPU/Disk/Battery gauges + Chat Mode toggle.
- `layout/RightColumn/RightColumn.tsx` — renders a **second, independently hardcoded** `HUBS` array (see 1.4), the `Orb`, and a node/link count panel computed purely from that static array (not the real graph).
- `layout/Topbar/Topbar.tsx` — personality pill cycles `assistant → developer → research`; modifier pill cycles `none → planner → quiet` (only shown when not "none"); model/provider, charging/graphMode, and memory-count pills.
- `layout/Dock/Dock.tsx` — toggles `graphOpen`, opens `ConversationPanel`, toggles `view` (settings/chat), mic button toggles `voiceActive` via `startVoice()`/`stopVoice()`.
- `graph/GraphCanvas/GraphCanvas.tsx` — see 1.4.
- `conversations/ConversationPanel/ConversationPanel.tsx` — conversation list/load/rename/delete; delete is gated behind a **hardcoded PIN "0523"** (`PinAuthModal.tsx`).
- `settings/SettingsView/SettingsView.tsx` — composes `SettingsLayout` + `SettingsSidebar` + one of `AIProviderSection`/`AppearanceSection`/`AboutSection` by local state.

### 1.2 Zustand stores

| Store | Owns | Confirmed consumers |
|---|---|---|
| `useAppStore.ts` | `view`, `graphOpen`, `graphFocused`, `activeHub`, `conversationPanelOpen`, `chatMode`, `graphLevel` (0/1/2), `actionFeedback(+Visible)` (5s auto-clear), `inspectorMessage` (3s auto-clear), `deletingConversationId`, `pendingCommand`, `graphMode` (2d/3d), `isCharging`, `voiceActive` | `LeftColumn`, `Topbar`, `Dock`, `GraphCanvas`, `ChatShell`, `ConversationPanel`, `Orb` (graphMode only), `uiActionExecutor.ts`, `usePowerMode.ts`, `useJarvisChat.ts` (pendingCommand) |
| `useAIStore.ts` | `provider`, `model`, `status`, `voiceStatus`, `isStreaming`, `error`, `memoryCount`, `openrouterKey`/`groqKey`/`geminiKey`, `personalityMode`, `modifier` | `Orb`, `Topbar`, `useEngineStatus.ts`, `useJarvisChat.ts`, `AIProviderSection.tsx`, `uiActionExecutor.ts` |
| `useConversationStore.ts` | `messages`, `currentConversationId`(+localStorage sync), `isTyping`, `streamingMessageId`/`streamingContent`, `streamingSearchQuery`, `currentConversationTitle`, `isStreaming`, `isSearching`/`searchingQuery` | `ChatShell`, `ChatFullView`, `ConversationPanel`, `GraphCanvas` (conversation-leaf click loads history), `useJarvisChat.ts`, `useConversationLoader.ts`, `uiActionExecutor.ts` |
| `usePersonalityStore.ts` | `mode`, `address`, formality/verbosity/humor/proactivity dials | **None — dead store**, superseded by `useAIStore.personalityMode`/`modifier` |

### 1.3 UI_ACTION protocol end-to-end

**Parsing**: `apps/desktop/src/utils/uiActionParser.ts` — regex `\[UI_ACTION:([^\]]+)\]` extracts `type:payload` tags and strips them from the display text (`parseUIActions` → `{cleanText, actions}`).

**Dispatch**: `apps/desktop/src/hooks/useJarvisChat.ts` calls `parseUIActions(fullResponse)` in the `onDone` callback of the streaming chat response (line ~290), then after a 500ms delay calls `executeUIActions(actions)` (line ~324-327). **Important gap**: on the voice-WebSocket path, `parseUIActions` is called only to strip tags for display (lines 65-85) — `executeUIActions` is never invoked there, so **UI actions embedded in voice responses are not executed**, only spoken/displayed with tags stripped.

**Execution**: `apps/desktop/src/utils/uiActionExecutor.ts` — the full current action set (verified by reading the switch statement):

`chat_mode_on`, `new_chat`, `delete_conversation`, `rename_chat`, `open_chat`, `chat_mode_off`, `graph_expand`, `graph_collapse`, `graph_open_hub`, `conversations_open`, `conversations_close`, `switch_provider`, `personality_mode`, `modifier`, `open_app`, `open_url`, `system_query`, `close_app`, `set_volume`, `lock_screen`, `confirm_action`, `list_dir`, `create_folder`, `open_file`, `show_explorer`, `delete_file` (routes to confirmation flow, not direct execution), plus a `default` no-op that logs "Unknown UI action".

**Cross-check against backend**: the backend does not appear to have a single canonical `SYSTEM_CAPABILITIES`/action-list module documented to the LLM — action names are embedded directly in prompt text inside `routes.py` (verified indirectly: no `core/router`/prompt registry module exists; `core/*` subpackages are empty stubs, see Section 2.7). This means the UI_ACTION vocabulary lives in two unsynchronized places: the frontend switch statement (source of truth for what's *handled*) and whatever prompt string in `routes.py` tells the LLM what's *available* — a drift risk flagged for Phase 9 (Capability Registry), see Section 5.

### 1.4 Graph/hub system

`GraphCanvas.tsx` hub taxonomy is **static and hardcoded**, and duplicated with slightly different data in two files:

```ts
// GraphCanvas.tsx
const LEAVES_DATA: Record<string, string[]> = {
  skills: ["Python","React","TypeScript","Rust","FastAPI","Tauri"],
  tools: ["Web Search","Memory","File System","Terminal","Browser","Calculator"],
  files: ["Documents","Downloads","Projects","Desktop","Pictures","Music"],
  notes: ["JARVIS Notes","Ideas","Tasks","Meeting Notes","Code Snippets"],
  models: ["gemini-2.5-flash","llama3.2:3b","qwen2.5-coder:3b","OpenRouter","Groq","nomic-embed-text"],
  worlds: ["Home","Work","Projects","Archive"],
  conversations: []
};
```

- `RightColumn.tsx` maintains a **second, independently-authored** `HUBS` array with the same 7 keys/colors but different literal leaf counts (e.g. skills=9 there vs. 6 actual entries in `GraphCanvas`'s `LEAVES_DATA`) — these two copies can and do disagree.
- The **only dynamic hub** is Conversations: its leaves are fetched live from the backend via `getConversations()`, capped at 8, built from real conversation title/preview. Clicking a leaf loads that conversation into `useConversationStore` and switches to chat mode.
- Everything else (Skills, Tools, Files, Notes, Worlds, Models) is compile-time hardcoded text with no backend/data binding — clicking these leaves does not fetch or act on real data.
- Rendering is a hand-rolled Canvas2D radial layout (`draw3DNode`/`draw2DNode`, `layout()`, `loop()` at 60fps rAF for 3D / 1s interval for 2D) with manual hit-testing — no scene graph library, no dynamic node registration API.

### 1.5 Tauri command surface

All commands registered in `invoke_handler!` in `apps/desktop/src-tauri/src/lib.rs` (lines 865-886):

**System queries**: `get_system_info`, `run_system_query` (enum: IpAddress/BatteryLevel/DiskSpace/TopProcesses/Uptime), `get_battery_info`, `get_disk_info`, `get_power_status`. Note: `get_system_info`'s GPU field is a **hardcoded placeholder array** (GTX 1650 + Intel Iris Xe), not real GPU detection (lines 46-59).

**Automation / OS control**: `find_application`, `open_application`, `close_application`, `set_volume` (Windows-only via `keybd_event`), `lock_screen`, `open_url_in_browser`, `shutdown_computer` (requires `confirmed:true`), `cancel_shutdown`, `restart_computer` (requires `confirmed:true`).

**File operations**: `list_directory`, `create_folder`, `read_file` (extension allowlist, 100KB cap), `open_file`, `show_in_explorer`, `rename_item`, `delete_file` (requires `confirmed:true`).

**Orphaned commands** (registered in Rust, never invoked from any frontend code — confirmed via grep across `src`):
- `find_application` — only called internally by `open_application`, never invoked directly from TS.
- `read_file` — wrapped in `systemApi.ts` as `readFile()`, but `readFile()` itself has zero call sites.
- `rename_item` — wrapped as `renameItem()`, also zero call sites.
- `shutdown_computer`, `cancel_shutdown`, `restart_computer` — not even wrapped in `systemApi.ts`; fully unreachable from the UI despite being implemented, registered, and PIN/confirmation-gated in Rust.

**Actually invoked**: `usePowerMode.ts` → `get_power_status`; `systemApi.ts` → `open_application`, `open_url_in_browser`, `run_system_query`, `close_application`, `set_volume`, `lock_screen`, `get_battery_info`, `get_disk_info`, `list_directory`, `create_folder`, `open_file`, `show_in_explorer`, `delete_file`; `LeftColumn.tsx` → `get_system_info`, `get_battery_info`, `get_disk_info` directly (bypassing `systemApi.ts`, an inconsistency worth normalizing before Phase 6+).

### 1.6 Services/hooks not covered above

- `services/jarvisApi.ts` — REST client, base URL hardcoded `http://localhost:8765`. `/chat` non-streaming `sendMessage` is **defined but never called** (app only uses `/chat/stream`). `getVoiceStatus` is also defined but never called. Owns the raw voice WebSocket client (`connectVoiceWebSocket`/`disconnectVoiceWebSocket`) with sequence-number staleness checking and 2s auto-reconnect.
- `hooks/useEngineStatus.ts` — polls `/health` every 30s, `/memories` count every 60s, syncs settings once on mount.
- `hooks/usePowerMode.ts` — polls `get_power_status` every 30s, drives `graphMode` (3d if charging, else 2d).
- `hooks/useConversationLoader.ts` — restores last conversation from `localStorage["jarvis_conversation_id"]` on first idle.

---

## 2. BACKEND ARCHITECTURE (services/jarvis-engine/)

All routes live in one file: `services/jarvis-engine/src/jarvis_engine/api/routes.py` (confirmed the only router — `main.py` does a single `app.include_router(router)`; the `core/router/` package is an empty stub, see 2.7).

### 2.1 Route inventory

| Method | Path | Behavior (verified from function body) |
|---|---|---|
| POST | `/search` | Calls `search_web()` + `format_search_results()`. |
| POST | `/voice/start` | Calls `voice_manager.initialize(handle_transcription)` using the shared handler from `transcription_handler.py`. |
| POST | `/voice/stop` | `voice_manager.shutdown()`. |
| GET | `/voice/status` | Returns `is_listening` + hardcoded `wake_word_model: "wake_up_jarvis"`. |
| POST | `/tts/stop` | `tts_engine.stop()`. |
| GET | `/tts/status` | Returns `is_speaking`, `voice`. |
| GET/POST | `/settings` | Read/write `personality_mode` (`assistant`/`developer`/`research`) and `modifier` (`none`/`planner`/`quiet`) — **inline string-literal validation, no enum class exists anywhere in `config.py`** (confirmed via grep). POST silently ignores invalid values rather than erroring. |
| POST | `/voice/status/update` | Broadcasts `voice_status` over `/ws/voice`. |
| POST | `/voice/input` | Full voice-text pipeline: automation/file-command detection → tries providers in a **hand-picked fixed order (ollama → groq → openrouter)**, which differs from `provider_manager`'s default order (Gemini → OpenRouter → Groq → Ollama) and from `/chat`'s provider loop. |
| WS | `/ws/voice` | Accepts, registers in `connected_clients`, loops `receive_text()` purely to detect disconnect — **server never processes inbound client messages**, effectively send-only despite being bidirectional. |
| POST | `/chat` | Non-streaming. Loads memories + last 24 messages, builds system prompt via personality/modifier, detects file-cmd/automation/browser/search intent, tries `provider_manager.providers` in order, saves messages, extracts memories. **No `is_pure_automation` fast-path** (unlike `/chat/stream` — the two "equivalent" endpoints diverge in behavior). |
| POST | `/chat/stream` | NDJSON streaming twin of `/chat`. Adds `search_started`/`search_complete`/`search_timeout` events, an `is_pure_automation` short-circuit that streams word-by-word with no LLM call, per-provider fallback if no tokens sent yet, and a background TTS speak+broadcast task on completion. |
| GET | `/health` | `voice_ready` = Kokoro-ready AND whisper-ready AND wake-word-ready (all `threading.Event.is_set()`). |
| GET/DELETE/PUT | `/conversation/{id}`, `/conversation/{id}/title` | Standard CRUD; DELETE cascades to messages; PUT rejects duplicate titles. |
| GET | `/providers` | `provider_manager.get_status()`. |
| POST | `/provider/switch` | Reorders the global provider list; **the `model` param is accepted but silently ignored** (see 2.3). |
| GET/POST/DELETE | `/memories`, `/memories/{id}` | CRUD; POST bypasses LLM extraction (direct create). |
| GET | `/memories/search?q=` | Keyword search via `get_relevant_memories`. |
| GET | `/conversations` | Last 10, hardcoded limit. |
| POST | `/memories/deduplicate` | Raw SQL, bypasses `memory_manager.py` entirely — deletes non-MIN-id rows grouped by lowercased 100-char content prefix. |
| POST | `/config/{openrouter,groq,gemini}-key` | Sets env var + `.env` file (via `dotenv.set_key`) + in-memory settings object, per provider. |

Dead model fields: `ChatRequest.provider`/`ChatRequest.model` (`core/models.py`) are defined but **never read** by any route — provider selection always goes through `provider_manager`, never the request body.

### 2.2 WebSocket event inventory (`/ws/voice`)

The endpoint itself never sends anything; all events are pushed via `broadcast_voice_event()` (routes.py), called from `/voice/status/update`, `/voice/input`, and the TTS background task in `/chat/stream`. Event types: `voice_status` (`{type, status}`), `voice_input` (`{type, text}`), `voice_response` (`{type, text}`).

**Sequence numbering — present and correct**:
```python
_voice_event_seq = 0
_voice_seq_lock = asyncio.Lock()

async def broadcast_voice_event(event: dict):
    global _voice_event_seq
    async with _voice_seq_lock:
        _voice_event_seq += 1
        event["seq"] = _voice_event_seq
        event["timestamp"] = time.time()
    ...  # fan out via client.send_json(event); prune dead clients
```
One global monotonic counter shared across all event types and all clients, incremented under an `asyncio.Lock` before assignment — guarantees clients can detect drops/reordering. Matches `tests/test_voice_ws_ordering.py`.

Voice pipeline (`voice_manager.py`) does not touch the websocket directly — it talks HTTP to `localhost:8765` (`/voice/status/update`, `/voice/input`) from background threads; those routes then fan out over the websocket.

### 2.3 Provider architecture

`providers/manager.py` (77 lines, read in full):

- Hardcoded priority order: **Gemini → OpenRouter → Groq → Ollama**.
- `chat()` iterates in order, first successful `is_available()` + `chat()` wins; on exception, logs and continues; if all fail, returns a canned apology with provider `"none"`.
- `set_active_provider(name, model)` reorders the **global singleton list** (affects all concurrent requests — documented as intentional). The `model` param is accepted but **not applied** — the docstring literally says "we don't dynamically change the model inside the provider for now."
- `/chat` and `/chat/stream` in routes.py do **not** call `provider_manager.chat()`/`.stream()` — they inline their own loop over `provider_manager.providers` with custom reordering for automation/file-command cases, meaning provider fallback behavior is implemented in (at least) three different places: `manager.py`, `/chat`+`/chat/stream`, and `/voice/input`.

**Cerebras — explicitly disabled, not a bug**: `manager.py` has a comment block stating Cerebras integration returns persistent HTTP 402 despite valid auth; `from .cerebras_provider import CerebrasProvider` is commented out and `CerebrasProvider()` is not in the providers list. `providers/cerebras_provider.py` (untracked, new) is fully implemented (auto-selects model from `["gpt-oss-120b","gemma-4-31b"]`) but is dead code from the running app's perspective. Notably, its `chat()` returns error **strings** instead of raising exceptions — if it were wired into the manager's try/except-continue loop as-is, a Cerebras failure would look like a successful (bad) response rather than trigger fallback to the next provider.

**Per-provider config** (`core/config.py`, defaults) vs. **live `.env`**:

| Provider | config.py default | `.env` current |
|---|---|---|
| Ollama | `OLLAMA_HOST=http://localhost:11434`, `OLLAMA_MODEL=phi4-mini` | `OLLAMA_HOST=http://10.79.209.37:11435` (LAN IP, different port than docs describe — see Section 3), `OLLAMA_MODEL=phi4-mini` |
| OpenRouter | `OPENROUTER_MODEL=google/gemma-4-27b-it:free` | `google/gemma-4-31b-it:free` (differs from code default) |
| Groq | `GROQ_MODEL=openai/gpt-oss-20b` | `openai/gpt-oss-20b` (matches; hardcoded fallback-on-error to `openai/gpt-oss-120b` in `groq_provider.py`) |
| Gemini | `GEMINI_MODEL=gemini-3.6-flash` | `gemini-3.6-flash` (matches) |
| Cerebras | `CEREBRAS_API_KEY` field exists | key present in `.env` but provider unwired (see above) |

Other provider-specific behavior: `gemini_provider.py` merges consecutive same-role turns and drops a leading assistant message (Gemini requires starting with `user`), and enforces its own 6000-token trim independent of the caller's 4000-token trim.

### 2.4 Database schema

`core/database.py` — four tables, `CREATE TABLE IF NOT EXISTS`:

- **`conversations`**: `id TEXT PK, title, created_at, updated_at`. Read/written entirely by `memory/conversation.py`.
- **`memories`**: `id TEXT PK, content, category (default 'general'), importance (default 5), created_at, last_accessed, access_count, source_conversation_id`. Read/written by `memory/memory_manager.py`; also raw-SQL-deleted-from directly in `/memories/deduplicate` (bypassing the manager module).
- **`messages`**: `id TEXT PK, conversation_id FK, role, content, timestamp, provider_used, model_used`. Written by `save_message` throughout routes.py; read by `get_conversation_messages`.
- **`settings`**: `key TEXT PK, value`. Used exclusively for `personality_mode`/`modifier` persistence. Note: `/voice/input` does **not** read personality settings — only `/chat` and `/chat/stream` call `get_system_prompt` with DB-backed personality/modifier.

Indexes: `idx_messages_conversation`, `idx_messages_conversation_time`, `idx_memories_created`, `idx_memories_conversation`.

No vector/embedding columns or tables exist — memory retrieval is pure SQL `LIKE`, not semantic (see 2.6). This is directly relevant to Phase 7 Memory Upgrade planning.

### 2.5 Web search tools

- `tools/web_search.py`: tries Tavily first if `TAVILY_API_KEY` set and `SEARCH_PROVIDER=="tavily"` (both true in current `.env`), falls back to DuckDuckGo (`duckduckgo_search.DDGS`) otherwise. Both wrapped in `asyncio.to_thread`.
- `tools/search_detector.py`: `needs_web_search()` regex-matches explicit search verbs or a set of realtime-info patterns (news/price/weather/score/who-is/etc). Invoked in both `/chat` and `/chat/stream`.

### 2.6 Memory manager

`memory/memory_manager.py`:
- **Extraction** (`extract_and_save_memories`): runs after every assistant reply in `/chat` and `/chat/stream` (wrapped in try/except so failures don't break streaming). Skips messages under 10 chars or if no Groq key. Sends user message + hand-written prompt to Groq (`groq/compound-mini` then `groq/compound` fallback), asking for JSON `{should_save, content, category, importance}`. Category clamped to `{personal, preference, project, goal, fact}` else `"general"`; importance clamped 1-10.
- **Retrieval** (`get_relevant_memories`): pure SQL — splits the user message into words >3 chars, builds an OR'd `LOWER(content) LIKE '%word%'` query, orders by `importance DESC, last_accessed DESC`, updates access stats on hit. **No embeddings, no vector search.**
- No personality-mode or system-query enum exists anywhere in `config.py` — both are plain string-literal validation inline in `routes.py`. Relevant if `tests/test_personality_modes.py`/`test_enum_system_queries.py` assume a shared enum module; they don't — the behavior is routes.py-local.

### 2.7 `core/*` subpackage stubs

Nine subpackages under `services/jarvis-engine/src/jarvis_engine/core/` — `event_bus`, `lifecycle`, `permissions`, `planner`, `router`, `security`, `configuration`, `memory` (note: distinct from and shadowed by the real, implemented top-level `jarvis_engine/memory/` module), and `logging` — each contains **only a 0-line empty `__init__.py`**. These are placeholder scaffolding for an architecture that has not been built yet. This is directly relevant to Phase 6+ planning: there is currently no event bus, no capability/permission system, no planner, and no dedicated router module — everything that exists today (routing, provider fallback, action dispatch) is implemented ad hoc inside `routes.py`, `manager.py`, and the frontend's `uiActionExecutor.ts`.

---

## 3. DRIFT CHECK

Comparing `docs/JARVIS_MASTER_STATUS.md`, `docs/CURRENT_STATUS.md`, `docs/DEVELOPMENT_LOG.md`, `docs/CLEANUP_REPORT.md`, `docs/OPUS_AUDIT_REPORT.md`, `docs/AUDIT_REPORT.md`, and `CLAUDE.md` against actual code:

1. **CLAUDE.md run command is wrong.** `CLAUDE.md:49-51` documents `uv run uvicorn jarvis_engine.main:app --reload --port 8000`. The actual documented/intended entrypoint is `services/jarvis-engine/start.py` (`uv run python start.py`), which binds `settings.JARVIS_HOST`/`JARVIS_PORT`; `config.py` sets the real default port to **8765**, not 8000. Every frontend service file hardcodes `http://localhost:8765` — port 8000 would not even work with the current frontend.

2. **Cleanup marked as reported but not executed.** `docs/CLEANUP_REPORT.md` recommends removing `ChatView.old.tsx`, `ChatView.old.test.tsx`, `AppShell.old.tsx`, `AppHeader.old.tsx` (and moving `test_foreground.py` out of `src/jarvis_engine/`). None of this has been done — all files still exist on disk unchanged.

3. **Retired model IDs still documented as current.** `docs/JARVIS_MASTER_STATUS.md` documents `gemini-2.5-flash`, `llama-3.3-70b-versatile`, and `llama3.2:3b` as current defaults. None of these three appear anywhere in current provider code or `.env`. Actual current models: `OLLAMA_MODEL=phi4-mini`, `GROQ_MODEL=openai/gpt-oss-20b`, `GEMINI_MODEL=gemini-3.6-flash`, `OPENROUTER_MODEL` code-default `google/gemma-4-27b-it:free` but `.env`-overridden to `google/gemma-4-31b-it:free`.

4. **CLAUDE.md provider description is backwards.** `CLAUDE.md:24` says "Ollama (primary), OpenRouter (fallback), Groq (for command generation)." Actual priority order in `manager.py` is Gemini → OpenRouter → Groq → **Ollama last**. Gemini isn't mentioned in CLAUDE.md at all, and the unwired Cerebras provider isn't mentioned anywhere in any doc.

5. **CLAUDE.md falsely claims no JS tests exist.** `CLAUDE.md:73`: "No JavaScript tests are currently configured." Actual: `apps/desktop/package.json` defines `test`/`test:run` via Vitest, and dozens of `*.test.tsx` files exist; `DEVELOPMENT_LOG.md` itself records "63/63 desktop tests pass."

6. **CURRENT_STATUS.md header contradicts its own body.** Header says "Phase 5 - Milestone 4: Advanced Voice Features / Status: In Planning," but the milestone table and "Recent Updates" section in the same file describe Milestones 1-4 (wake word, voice pipeline, TTS, advanced voice features) as Complete with implementation specifics — the header was evidently never updated after shipping.

7. **TTS voice/config details stale even within the Phase 5 section.** `CURRENT_STATUS.md` says "en-GB-RyanNeural... British accent... +10% speed." Actual: `EDGE_TTS_VOICE=en-US-AndrewMultilingualNeural` (American), `EDGE_TTS_RATE=+5%`. Additionally, the doc never mentions Kokoro TTS, which is now the **primary** streaming engine (`tts_engine.py`), with edge-tts demoted to fallback — an entire engine swap undocumented.

8. **Ollama host/port drift across docs and code.** `DEVELOPMENT_LOG.md` records `http://10.79.209.37:11434`. Current `.env` has the same IP but port **11435**. The stray root-level `diagnose.py` still hardcodes the old port `11434` and a model (`qwen2.5:7b`) that appears nowhere in current config — running it today would silently hit a dead/wrong endpoint.

9. **JARVIS_MASTER_STATUS.md's entire "Section 14" is pre-Phase-5 and now false.** It states Voice/STT, TTS, and Wake Word are all "Not started," dated "Last audited: 2026-08-16" — three days before Phase 5 shipped (2026-08-19 per `CURRENT_STATUS.md`). The doc's folder-structure section is also stale: it omits `src-tauri` automation/safety commands, the entire `voice/` module, and `providers/gemini_provider.py`/`cerebras_provider.py`.

10. **OPUS_AUDIT_REPORT.md cites a function that no longer exists.** It references `execute_powershell_command()` in `lib.rs` as the location of a command-injection finding (SEC-002). No such function exists in current `lib.rs` — the code now shells out via a bundled, parameterized PowerShell script (`get_find_app_script_path()` + `-File` invocation), which looks like exactly the fix the audit recommended, but the doc still points at stale code.

11. **Doc "defaults" don't match the live, running configuration.** Even where `JARVIS_MASTER_STATUS.md` correctly states the code-level default for `OPENROUTER_MODEL` (`google/gemma-4-27b-it:free`, matching `config.py`), the actually-running `.env` overrides it to `google/gemma-4-31b-it:free` — so a reader trusting the doc's default would still be wrong about what's live.

---

## 4. TECH DEBT INVENTORY

### 4.1 TODO/FIXME/HACK/XXX comments

None found. A case-insensitive grep across `apps/desktop/src`, `apps/desktop/src-tauri/src`, and `services/jarvis-engine/src` for `TODO|FIXME|HACK|XXX` returned zero matches. This means none of the debt below is self-flagged in code — it was found only by reading files and cross-referencing against docs/status reports.

### 4.2 Dead code / cleanup candidates

- **`cerebras_provider.py`** — fully implemented, intentionally unwired (HTTP 402 from Cerebras account). Not a bug, but undocumented anywhere; should either be finished (once billing resolved) or removed with a note, and mentioned in provider docs either way.
- **`execute_powershell` / similar retired names** — grep of current `lib.rs` finds no such function; the audit-report reference to it (`OPUS_AUDIT_REPORT.md:555`) is stale, not the code.
- **`diagnose.py`** (repo root, untracked) — one-off latency-debugging script with hardcoded stale IP/port (`10.79.209.37:11434`, one port off from live `.env`) and a model (`qwen2.5:7b`) not present in any current config. Not a reusable tool; candidate for deletion.
- **`test_results.txt`** (`services/jarvis-engine/`, untracked) — not pytest output; a raw manual-run transcript comparing personality-mode responses, including at least one failed/timeout run. Stale artifact, safe to delete.
- **`update_log.py`, `update_log2.py`, `update_log3.py`** (repo root, tracked) — three near-duplicate one-shot scripts, each just appends one hardcoded historical entry to `docs/DEVELOPMENT_LOG.md`. Served their purpose once; now dead weight, re-running any would duplicate log entries.
- **`services/jarvis-engine/tests/test_restart_1.py`, `test_restart_2.py`** — filenames match pytest's collection pattern but contain no `test_*` functions (only a `run_tests()` guarded by `__main__`), so pytest imports them and silently finds zero tests — dead weight in the suite, should be renamed or moved out of `tests/`.
- **`services/jarvis-engine/tests/run_live_test.py`** — same shape, but filename doesn't match `test_*.py` so pytest ignores it; a manual smoke-test script requiring a live Ollama instance.
- **`services/jarvis-engine/src/jarvis_engine/test_foreground.py`** — sits inside the installable package (`src/jarvis_engine/`), not `tests/`; prints hardcoded YouTube-search URLs at import time. `pytest` won't collect it (testpaths restricted to `tests/`) but it would ship inside the built package. Already flagged by `CLEANUP_REPORT.md`, not yet acted on.
- **`services/jarvis-engine/test_api.py`, `test_dedup.py`, `test_yt.py`** — live at the `services/jarvis-engine/` root (sibling to `pyproject.toml`), outside `tests/`, so not covered by the pytest suite at all — orphaned/inconsistent placement.
- **Frontend `.old.tsx` files** — `AppHeader.old.tsx`, `AppShell.old.tsx`, `ChatView.old.tsx` (+ `.old.test.tsx`) — recommended for removal by `CLEANUP_REPORT.md`, still present. Combined with the larger orphaned component systems in Section 1.1 (`ai-core/*`, the unused chat sub-component tree, `usePersonalityStore`), there is a substantial amount of dead frontend code from an apparently abandoned refactor that should be pruned or consciously revived before Phase 6+ builds on top of it.
- **Nine empty `core/*` stub packages** (Section 2.7) — placeholder-only, no implementation. Either build them out for Phase 6+ or remove them so the package layout doesn't mislead readers into thinking an event bus/planner/security layer already exists.
- **Per `CLEANUP_REPORT.md` (not independently re-verified this pass but structurally plausible given no related changes in git status)**: unused `chromadb`/`sentence-transformers` dependencies in `pyproject.toml` (~700MB, no imports found), and a duplicate `SearchResult` class / dead `format_search_results()` remnants in `web_search.py`.

### 4.3 In-flight/uncommitted work (from git status, secrets not printed)

`services/jarvis-engine/.env` and `data/jarvis.db` are modified (expected runtime state); `voice/transcription_handler.py` is new/untracked but already live (imported by `main.py`); `src-tauri/Cargo.toml`/`lib.rs` modifications align with the CSP/mutex-panic hardening claimed in `CURRENT_STATUS.md`; provider files (`gemini_provider.py`, `manager.py`, etc.) and several new test files under `tests/` are mid-flight and not yet reflected in any status doc — expect the docs to keep drifting until these are committed and the status docs are updated alongside.

---

## 5. READINESS ASSESSMENT FOR PHASE 6+

### Dynamic UI Widgets (Phase 8.5)

**Not supported today — needs a new rendering pattern.** The current frontend has no component-registry or dynamic-render mechanism: `App.tsx` statically composes a fixed tree, `GraphCanvas`'s hub taxonomy is hardcoded TypeScript data (`LEAVES_DATA`/`HUBS`, duplicated in two files), and the UI_ACTION system (`uiActionExecutor.ts`) is a hand-written `switch` statement mapping a closed, hardcoded set of string action-types to specific store mutations and API calls — there is no path from "LLM emits an arbitrary widget spec" to "React renders it." The closest thing to a registration pattern is the UI_ACTION switch itself, which is informal (no schema, no validation, silently no-ops on unknown types) and would need to be replaced or wrapped by a real component registry (e.g. a `{type, props}` → component lookup table) plus a rendering surface (a panel/slot the registry can mount into) before dynamic widgets are feasible. Also note the voice-response path never calls `executeUIActions` at all, so whatever registry is built must be explicitly wired into both the streaming-chat and voice-response paths.

### Capability Registry (Phase 9 M1)

**Would be built from scratch, but has three candidate patterns to unify or supersede.** There are currently three independent, unsynchronized "what can JARVIS do" surfaces: (1) the frontend's `uiActionExecutor.ts` switch (source of truth for what's *handled* client-side), (2) Tauri's `#[tauri::command]` registration in `lib.rs` (source of truth for what's *available* at the OS layer — and already has orphaned/unreachable commands like `shutdown_computer`/`rename_item`/`read_file` that a registry would need to reconcile), and (3) whatever prompt text in `routes.py` tells the LLM is available (not backed by a shared constant/enum anywhere — confirmed no enum classes exist in `config.py`). None of these read from or write to a common source. The nine empty `core/*` stub packages (`permissions`, `router`, `planner`, etc.) suggest a registry was anticipated architecturally but never implemented. Building Phase 9 M1 means picking one of these three as the canonical list (or introducing a fourth, shared one) and having the other two generate from it rather than duplicate it by hand.

### Memory Visualization (Phase 7 M1)

**The graph's "Models" hub name is close, but there is no "Memories" hub at all today**, and nothing memory-related is wired into `GraphCanvas`. The hub set is hardcoded to Skills/Tools/Files/Notes/Worlds/Models/Conversations — Conversations is the only backend-connected hub (fetches real titles via `getConversations()`), and even that shows conversations, not memories. Adding a Memories hub would need: (1) a new hub entry in both `GraphCanvas.tsx` and `RightColumn.tsx`'s duplicate `HUBS` arrays (or better, deduplicating those first), and (2) a fetch against the existing `/memories` and `/memories/search` endpoints. The available data shape to visualize, from the `memories` table (`core/database.py`) and `memory_manager.py`, is: `id, content (free text), category (personal|preference|project|goal|fact|general), importance (1-10), created_at, last_accessed, access_count, source_conversation_id`. There is no embedding/vector data and no relationship/graph structure between memories — retrieval is pure SQL `LIKE` keyword search, so any "visualization" beyond a flat list-by-category/importance (e.g. a semantic map or memory-to-memory graph) would require adding vector storage first, which doesn't exist anywhere in the current schema.

---

## Appendix: Key files referenced

- Frontend: `apps/desktop/src/App.tsx`, `src/stores/*.ts`, `src/utils/uiActionParser.ts`, `src/utils/uiActionExecutor.ts`, `src/hooks/useJarvisChat.ts`, `src/components/graph/GraphCanvas/GraphCanvas.tsx`, `src/components/layout/RightColumn/RightColumn.tsx`, `apps/desktop/src-tauri/src/lib.rs`
- Backend: `services/jarvis-engine/src/jarvis_engine/api/routes.py`, `core/config.py`, `core/database.py`, `core/models.py`, `providers/manager.py` + `providers/*.py`, `memory/memory_manager.py`, `memory/conversation.py`, `voice/*.py`, `main.py`, `start.py`
- Docs audited for drift: `CLAUDE.md`, `docs/JARVIS_MASTER_STATUS.md`, `docs/CURRENT_STATUS.md`, `docs/DEVELOPMENT_LOG.md`, `docs/CLEANUP_REPORT.md`, `docs/OPUS_AUDIT_REPORT.md`, `docs/AUDIT_REPORT.md`
