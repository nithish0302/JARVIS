# JARVIS Current Status

Last updated: 2026-08-19

## Current phase

Phase 5 - Milestone 4: Advanced Voice Features
Status: In Planning
Previous: Text-to-Speech (TTS) - Complete

**Phase 5 - Voice Capabilities**

The system can now detect the "wake up jarvis" wake word via openWakeWord in a background thread, and record speech.

## Current milestone

**Milestone 1 - Wake Word Detection**

Status: **Complete**

JARVIS is now capable of listening for the "wake up jarvis" wake word continuously without blocking the backend. When triggered, it records the user's speech and transcribes it locally using faster-whisper. The UI microphone button connects to the FastAPI backend to start/stop the background voice service.


## Completed milestones

| Milestone                                                               | Status                    | Result                                                                                                                                        |
| ----------------------------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 - Milestone 1: Tauri template cleanup                           | Complete                  | Removed template greeting/opener behavior and renamed the canonical desktop app to JARVIS.                                                    |
| Phase 0 - Milestone 2: Design foundation                                | Complete                  | Added semantic token and global-style foundations.                                                                                            |
| Phase 0 - Milestone 3: Reusable UI primitives                           | Complete                  | Added Button, IconButton, Input, Card, StatusIndicator, and the shared `cn` utility.                                                          |
| Phase 0 - Milestone 3 refinement                                        | Complete                  | Added documented input focus and button interaction states using semantic tokens.                                                             |
| Phase 0 - Milestone 4: Application shell                                | Complete                  | Added static layout structure, semantic layering, and single-main-scroll ownership without feature UI.                                        |
| Phase 0 - Milestone 5: Design System Foundation                         | Complete                  | Added the canonical semantic design-token specification and expanded the token implementation.                                                |
| Phase 0 - Milestone 6A: Base UI Component Library - Core Primitives     | Complete                  | Added Button, IconButton, Card, Panel, Badge, Divider, Field, and Input in self-contained component folders.                                  |
| Phase 0 - Milestone 6B: Base UI Component Library - Extended Primitives | Complete                  | Added Textarea, Select, Checkbox, Switch, Spinner, Skeleton, and StatusIndicator in self-contained component folders.                         |
| Phase 1 - Milestone 1: Header and Status Bar                            | Complete                  | Added persistent application navigation and a presentation-only status bar to the application shell.                                          |
| Phase 1 - Milestone 2: AI Core (Idle Experience)                        | Complete                  | Added the centralized IdleView including the animated AI Core, typography, and placeholder suggestion grid.                                   |
| Phase 1 - Milestone 3: Chat Conversation Area                           | Complete                  | Added the scrollable ConversationArea, MessageList, MessageBubble, MessageAvatar, and TypingIndicator components with static layout toggling. |
| Phase 1 - Milestone 4: Chat Composer (Input Area)                       | Complete                  | Added ChatComposer, ComposerToolbar, and SendButton components with auto-grow and character constraint presentation.                          |
| Phase 1 - Milestone 5: Settings UI                                      | Complete                  | Added SettingsView, SettingsLayout, SettingsSidebar, AIProviderSection, AppearanceSection, and AboutSection.                                  |
| Phase 1 - Milestone 6: Desktop Polish                                   | Complete                  | Refined UI with Framer Motion transitions, strict adherence to max-width and scrollbar styles, added focus rings, updated brand header.     |
| Phase 2 - Milestone 1: Zustand Stores + Remove Mock Data                | Complete                  | Introduced useConversationStore, useAIStore, usePersonalityStore, useAppStore. Refactored App and ChatView to rely on global state.           |
| Phase 2 - Milestone 2: jarvis-engine FastAPI Server                     | Complete                  | Built FastAPI server foundation, SQLite storage, and provider abstraction.                                                                    |
| Phase 2 - Milestone 3: Ollama Real AI Connection                        | Complete                  | Connected Ollama to JARVIS Engine to provide real AI responses.                                                                               |
| Phase 2 - Milestone 4: Connect Desktop UI to jarvis-engine              | Complete                  | Created jarvisApi client, useJarvisChat hook, useEngineStatus hook, and integrated into ChatView and AppShell StatusBar.                      |
| Phase 2 - Milestone 5: OpenRouter Fallback Provider                     | Complete                  | Integrated OpenRouter as a fallback provider when Ollama is offline, updating provider configs and tests.                                     |
| Phase 2 - Milestone 6: Streaming Responses                              | Complete                  | Integrated token streaming from Ollama backend via FastAPI to the React frontend UI for real-time chat.                                       |
| Phase 2 - Milestone 7: Long Term Memory System                          | Complete                  | Integrated long-term memory system using SQLite, extracting facts, and injecting context into system prompts.                                 |
| Phase 2 - Milestone 8: Live StatusBar & Settings                        | Complete                  | Enhanced AppShell StatusBar with live state tracking, memory count fetching, and AI Provider settings persistence.                            |
| Phase 2 - Milestone 9: Conversation Persistence                         | Complete                  | Persisted conversation IDs in local storage, implemented automatic context reloading on startup, and added /conversations endpoint.           |
| Phase 3 - Milestone 1: Web Search Capability                            | Complete                  | Integrated DuckDuckGo search for real-time information retrieval and injected search results into AI prompt context.                          |
| Phase 3 - Milestone 2: Complete UI Overhaul                             | Complete                  | Replaced the original chat-app interface with the complex HUD layout, refined graph physics, and integrated live system stats via Tauri `sysinfo`. |
| Phase 3 - Milestone 3: Tavily Search + Sources UI                       | Complete                  | Migrated to Tavily Search API and integrated `SearchBadge` and `SourcesList` HUD UI to display live search context and clickable source citations. |

| Phase 3 - Milestone 4: [UI_ACTION] Protocol                   | Complete                  | Introduced the UI Action protocol, letting JARVIS command the React frontend (opening hubs, switching views) via invisible tags safely parsed from its streaming responses. |
| Phase 3 - Milestone 5: Background Search                      | Complete                  | Integrated parallel background search and injected results directly into conversation history for real-time live context.                                     |
| Phase 4 - Milestone 0: Groq Provider                          | Complete                  | Integrated Groq API for blazing-fast inference using Llama 3.3 70B models.                                                                                  |
| Phase 4 - Milestone 1: Desktop Automation                     | Complete                  | Implemented a Dynamic Command Execution System using Rust/Tauri to securely generate and execute PowerShell commands based on user intent.                  |
| Phase 4 - Milestone 2: Foreground Search                      | Complete                  | Implemented robust intent matching to intelligently open URLs visually in the user's browser, replacing background search when visual results are preferred. |
| Phase 4 - Milestone 3: File System Operations                 | Complete                  | Extended Rust backend with directory listing, file reading, file deletion, and folder creation, integrated safely into JARVIS's command generation prompts. |
| Phase 4 - Milestone 4: Safety Layer                           | Complete                  | Implemented comprehensive safety system with destructive action detection, user confirmation UI, and shutdown/restart commands with mandatory confirmation. |
| Phase 4 - Milestone 5: 3D/2D Power Mode                       | Complete                  | Integrated power status polling to dynamically switch the graph between 3D mode (charging) and 2D mode (battery), along with a power indicator pill in the Topbar. |
| Phase 5 - Milestone 1: Wake Word Detection                    | Complete                  | Integrated openWakeWord and faster-whisper to continuously listen for "wake up jarvis", record user speech, and transcribe it.                              |
| Phase 5 - Milestone 2: Voice Chat Pipeline                    | Complete                  | Connected voice transcription to chat pipeline via WebSocket, enabling voice input to appear in chat with 🎤 prefix and receive JARVIS responses.           |
| Phase 5 - Milestone 3: TTS Voice Output                       | Complete                  | Integrated edge-tts with en-GB-RyanNeural voice, TTS interrupt detection via microphone energy threshold, speaking status orb synchronization (violet), and UI_ACTION tag stripping before speech. |

**Phase 4 - Additional Capabilities**

Status: **Complete**

The fifth milestone of Phase 3 is complete. The JARVIS system now supports parallel background search. The AI response streams immediately while the web search executes in the background. Search context is appended to the conversation history as a system message so that follow-up questions can reference the live information, and the sources are piped to the frontend in the final "done" chunk.

**Phase 4 - Additional Providers**

**Milestone 1 - Desktop Automation**

Status: **Complete**

JARVIS can now execute dynamic automation commands generated via LLM through a safe Rust execution engine.

The next milestone for Phase 4 will be expanding additional capabilities.

## Current technology stack

### Canonical desktop application

- Tauri v2 with Rust backend
- React 19
- TypeScript
- Vite
- Tailwind CSS v4 with PostCSS
- Framer Motion
- clsx
- lucide-react
- Vitest, Testing Library, ESLint, and Prettier development tooling

### Documented stack not currently used by the canonical desktop manifest

- Zustand is an accepted architecture decision for future global state, but it
  is not currently listed in `apps/desktop/package.json` and no store exists.

### Present but not yet documented as active product usage

- `three`, `@react-three/fiber`, and `@react-three/drei` are present in the
  canonical desktop package manifest. No current JARVIS feature or project
  document establishes their use.

## Active architecture decisions

| ADR  | Decision                                                                    | Status                                      |
| ---- | --------------------------------------------------------------------------- | ------------------------------------------- |
| 0001 | Use Tauri v2 instead of Electron.                                           | Accepted and active.                        |
| 0002 | Use Zustand for global state; retain React state for local component state. | Accepted and active for future state needs. |
| 0003 | Use a 70% modern desktop / 30% Iron Man-inspired design language.           | Accepted and active.                        |
| 0004 | Keep AI providers independent through an abstraction layer.                 | Accepted and active for future AI work.     |

## Tracking maintenance

- Update this document after every approved milestone so it reflects the latest
  verified repository state.
- Append, rather than rewrite, milestone history in `DEVELOPMENT_LOG.md`.

## Recent Updates

**Bug Audit & Fixes (2026-08-17)**
- Resolved race condition in AI search response (Search now correctly blocks AI until results are fetched and injected).
- Fixed `asyncio` blocking issues in `web_search.py` by offloading `tavily` and `duckduckgo` calls to threads.
- Rewrote `search_detector.py` with robust regex handling for UI exclusion and real-time triggers.
- Resolved frontend state bugs: disabled new chat during stream, fixed `setTimeout` leak, and added a visual search indicator.
- Addressed Tauri security: Enabled strict CSP in `tauri.conf.json` and fixed mutex panics and integer overflows in `lib.rs`.
- Desktop Automation refinements: Supported multiple app openings via JSON arrays, fixed browser URL opening, expanded AppData search logic in Rust, and added ReactMarkdown to chat for clean display.

**Phase 5 Updates (2026-08-19)**
- **Milestone 1**: Implemented continuous background wake word detection using openWakeWord and faster-whisper. 
- Integrated a daemonized background thread in `jarvis-engine` to prevent blocking the FastAPI server.
- Added `/voice/start`, `/voice/stop`, and `/voice/status` endpoints.
- Connected the microphone button in the React UI (`Dock.tsx`) to toggle the backend listening state.
- **Milestone 2**: Connected voice transcription to chat pipeline via WebSocket and `/voice/input` endpoint.
- Voice inputs now appear in chat with 🎤 prefix and receive full JARVIS responses.
- Added WebSocket endpoint `/ws/voice` for real-time voice events with auto-reconnect.
- Fixed multiple wake word detections with is_processing flag.
- Improved transcription accuracy by upgrading from base.en to small.en Whisper model.
- **Milestone 3**: Voice pipeline optimization and performance fixes.
- Implemented direct command mapper for instant execution of common commands (open apps, lock screen, volume control) without LLM.
- Fixed GPU usage: Adaptive frame rate (60fps in 3D mode, 1fps in 2D mode) reduces iGPU from 100% to near-zero when idle.
- Removed double transcription bug and excessive debug logging.
- Configured Ollama as primary provider for voice commands on HP laptop (http://10.79.209.37:11434).
- **Milestone 4**: Text-to-Speech (TTS) Voice Output.
- Integrated edge-tts library with en-GB-RyanNeural voice for natural British accent speech output at +10% speed.
- Implemented TTSEngine class with pygame for audio playback, async/threading for non-blocking operation.
- Added TTS interrupt detection: when user speaks (audio energy > 0.02), TTS immediately stops to prevent overlap.
- Enhanced orb visualization with violet (#a78bfa) "speaking" status that syncs via WebSocket voice_status events.
- Implemented UI_ACTION tag stripping before TTS to prevent JARVIS from reading technical tags aloud.
- Added /tts/stop and /tts/status control endpoints for manual TTS management.
- JARVIS now speaks every chat response and direct voice command result automatically.
