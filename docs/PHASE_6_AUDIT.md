# JARVIS Phase 6 Audit — Performance, UI/UX, Code Quality

**Purpose**: Follow-on to `docs/PHASE_0_5_ARCHITECTURE_AUDIT.md` (audited 2026-08-21). This pass does **not** re-derive claims that audit already verified and that are still true — it re-checks them against current code, reports what changed, and covers what's new since: Personality Modes (PIN hardening on the delete flow), and the live audio-level waveform feature shipped tonight. Audit-only, no code modified.

Audited: 2026-08-23. Repo root: `D:\JARVIS`.

---

## PART 1 — PERFORMANCE / MEMORY (RAM findings — read this first)

### 1.1 Backend RAM: measured, not estimated

The backend was already running live (PID 14704, the uvicorn `--reload` worker — the parent launcher PID 16948 stays at ~5-30MB and isn't the process doing work) with a real frontend WebSocket client connected (`Get-NetTCPConnection` showed 1-3 `Established` connections to port 8765 throughout), so the `audio_level` broadcast path was actually active — this is the real-world scenario, not an idle-with-nobody-listening test.

Sampled Working Set (`WorkingSet64`, actual resident RAM) every 30s for 5 minutes via `Get-Process`:

| Elapsed | WS (MB) | PM (MB) |
|---|---|---|
| 0s | 55.73 | 4603.77 |
| 30s | 56.58 | 4603.77 |
| 60s | 56.89 | 4603.73 |
| 90s | 57.12 | 4603.77 |
| 120s | 57.38 | 4603.80 |
| 150s | 57.54 | 4603.80 |
| 180s | 57.62 | 4603.77 |
| 210s | 57.75 | 4603.77 |
| 240s | 57.78 | 4603.77 |
| 270s | 58.02 | 4603.77 |
| **300s** | **47.79** | 4603.77 |

**Verdict: plateau, not a leak.** Working Set rose modestly (~55.7 → ~58.0 MB, +2.3MB) over the first 4.5 minutes, then a GC pass at the 5-minute mark dropped it back to 47.8MB — a sawtooth pattern (rise-then-reclaim), which is the signature of normal allocator/GC churn, not a monotonic leak. A real leak would keep climbing past the GC cycle; this didn't. Private Memory (`PrivateMemorySize64`) — mostly reserved virtual address space from ONNX Runtime / torch / numpy arenas at process startup — stayed completely flat at 4603.7-4603.8MB the entire time, confirming nothing is growing the process's committed footprint. (Private Memory ≫ Working Set here is normal for ML-library-heavy Python processes: most of that 4.6GB is reserved-but-not-resident address space, not actual RAM pressure.)

**Caveat**: 5 minutes is one GC cycle's worth of evidence, not a multi-hour soak test. The sampling script kept running in the background past the 5-minute mark; the full 11-minute series confirms the same pattern — bounded oscillation, not a climb:

| Elapsed | WS (MB) | PM (MB) |
|---|---|---|
| 330s | 48.23 | 4604.77 |
| 360s | 48.42 | 4604.77 |
| 390s | 62.61 | 4604.71 |
| 420s | 63.16 | 4604.71 |
| 450s | 63.72 | 4604.68 |
| 480s | 63.79 | 4604.68 |
| 510s | 63.89 | 4604.68 |
| 540s | 65.23 | 4605.94 |
| 570s | 64.10 | 4604.71 |
| 600s | 63.34 | 4604.71 |
| **630s** | **63.49** | 4604.71 |

Across the full 11 minutes: two GC-driven rise/reclaim cycles (peaked ~58MB then dropped to ~48MB at the 5-minute mark; rose again to ~63-65MB and has been flat/oscillating there since ~6.5 minutes in). Private Memory stayed within 4603.7-4606MB the entire time — effectively flat. This is a stable oscillation band, not a trend line with positive slope. Still not a multi-hour soak test, but 11 minutes of live operation with an active client shows no compounding growth.

### 1.2 `useMicLevelStore.ts` rolling buffer — bounded, verified by reading the code

```ts
const HISTORY_SIZE = 40;
...
history: [...get().history, clamped].slice(-HISTORY_SIZE),
```

Every push does a spread-and-slice, so `history` is capped at exactly 40 entries (~320 bytes as a JS number array) no matter how long the session runs. `level` is a single scalar, not an accumulator. **No unbounded growth is possible here** — this is a hard cap, not a "usually stays small" heuristic.

Honesty note: this is a **static code proof**, not a measured browser-heap number. Actually attaching a memory profiler to the Tauri webview's devtools requires an interactive session I don't have access to from here (no way to drive the app's UI or open devtools headlessly). Given the buffer is provably bounded by a `slice()` on every write, a live heap snapshot would not change this conclusion — but if you want an actual before/after heap-size screenshot for the record, that needs a human at the keyboard with devtools open.

### 1.3 `audio_level_bus.py` queue — self-draining, not backlog-prone in practice

```python
def get_latest_level():
  latest = None
  try:
    while True:
      latest = _level_queue.get_nowait()
  except queue.Empty:
    pass
  return latest
```

`get_latest_level()` drains the **entire** queue on every call, keeping only the newest item — this is the intended "coalesce to latest" design, confirmed correct. The queue itself has no `maxsize`, so in principle if the broadcast task's event loop were ever fully blocked for a stretch (not throttled-slow, but actually stalled — e.g. by something else hogging the single asyncio loop), items would accumulate for that duration. In practice this is a non-issue: each queued item is one Python `float` (~24-32 bytes plus a deque node), the producer rate is ~12.5Hz (wake_word) or ~15.6Hz (speech_recorder) — both close to the 12Hz drain rate — and the very next time the loop runs, the whole backlog is drained to one item regardless of how large it got. There's no scenario where this compounds across restarts or survives a stall; it's self-correcting the moment the event loop resumes. Not a leak, and the 5-minute RAM trend above (flat Private Memory, plateauing Working Set) is consistent with there being no meaningful backlog during normal operation.

### 1.4 Bottom line for Part 1

No leak found in any of the three places named in the task. Backend: measured flat/plateauing over 5 minutes live. Frontend history buffer: provably bounded by `slice(-40)`. Backend queue: self-draining by construction, and the measured RAM trend doesn't show the compounding you'd expect if it weren't.

---

## PART 2 — UI/UX AUDIT

### 2.1 Graph hubs — functional vs. decorative (honest breakdown)

Only **Conversations** is real. Confirmed unchanged from the 08-21 audit — re-verified against current `GraphCanvas.tsx`/`RightColumn.tsx`:

| Hub | Data source | Status |
|---|---|---|
| **Conversations** | `getConversations()` — live backend fetch, capped at 8 | **Functional.** Click a leaf → loads real conversation history into `useConversationStore`, switches to chat mode. |
| Skills | `LEAVES_DATA.skills` hardcoded array (`Python, React, TypeScript, Rust, FastAPI, Tauri`) | **Decorative.** Compile-time text, clicking does nothing beyond the canvas's own hover/select visual state. |
| Tools | hardcoded array | **Decorative.** Same. |
| Files | hardcoded array | **Decorative.** Notably: there's a fully working file-operations backend (`list_directory`, `create_folder`, `open_file`, `show_in_explorer`, `delete_file` all wired and used elsewhere in the app via `systemApi.ts`) — this hub doesn't call any of it. It's the single biggest gap between "looks wired" and "is wired." |
| Notes | hardcoded array | **Decorative.** No notes backend exists anywhere in the codebase. |
| Models | hardcoded array, and **stale** — lists `gemini-2.5-flash`, `llama3.2:3b`, `qwen2.5-coder:3b`, `nomic-embed-text`, none of which match any current provider config (`.env` / `config.py` now show `gemini-3.6-flash`, `phi4-mini`, `openai/gpt-oss-20b`, no embedding model in use at all) | **Decorative, and actively misleading** — a user clicking this hub sees model names JARVIS isn't actually using. |
| Worlds | hardcoded array | **Decorative.** No concept of "worlds" exists in the backend at all. |

**Also unchanged from 08-21**: `RightColumn.tsx` and `GraphCanvas.tsx` still each maintain their own independent hardcoded hub-leaf-count arrays, and they still disagree — `RightColumn.HUBS` says skills=9/tools=6/files=8/notes=7/worlds=5/models=6, while `GraphCanvas.HUBS` (derived from its own `LEAVES_DATA.length`) computes skills=6/tools=6/files=6/notes=5/worlds=4/models=6. Two sources of truth for the same numbers, silently out of sync. Nobody using the UI "productively" today gets real functionality from six of the seven hubs — worth being direct about that with anyone evaluating the app's current capability, since the graph visually presents all seven as equally real.

### 2.2 Personality Mode / Modifier indicators — not discoverable without prior knowledge

Read `Topbar.tsx` in full. Findings:

- The personality pill shows only the raw mode word (`ASSISTANT` / `DEVELOPER` / `RESEARCH`) with a color-coded dot. Its only affordance hint is an HTML `title` tooltip (`"Personality Mode: ASSISTANT (Click to switch)"`) that requires hovering — nothing in the visible UI says "click me" or explains what the three modes *do* differently.
- The modifier pill is **completely absent from the screen** whenever `modifier === "none"` (the default) — `{modifier !== "none" && (...)}`. A new user has no visual cue this feature exists at all until they either stumble into it by clicking the (undiscoverable) personality pill enough times, or ask JARVIS out loud to "turn on planner mode."
- Neither pill has a label, icon-with-legend, or first-run hint. Compare to the memory-count pill and status pill next to them, which are at least self-explanatory by their content (`"12 MEMORIES"`, `"IDLE"`) — the personality/modifier pills read as raw enum values with no framing.

**Verdict**: requires already knowing what they mean. This is a real onboarding gap, not just a nice-to-have — a first-time user has no path to discovering "click this to change how JARVIS talks to you" short of documentation or being told.

### 2.3 Waveform / "mic is live" clarity

Read `Dock.tsx`/`Dock.css` (as modified this session) and `Orb.tsx`/`Orb.css`. The waveform lives on the Dock's mic button (bottom-left dock rail, `position: absolute; bottom: 275px`) as a glow ring that scales/brightens with `useMicLevelStore.level`, separate from the Orb's own status ring in the right column (which shows `IDLE`/`LISTENING`/`SPEAKING`/`THINKING` text + color, but does **not** react to raw mic amplitude — only to discrete voice-status states).

Assessment, thinking as someone who hasn't been told what it is:

- **Positive**: the ring only appears/pulses when `voiceActive` is true (`ringOpacity = voiceActive ? ... : 0`), so at least it's not pulsing when voice detection is fully off — that's a correct, honest signal.
- **Ambiguity risk**: the mic button and the Orb's "IDLE" status live in two different UI regions (dock rail vs. right column), and nothing visually connects them. A user watching the Orb say "IDLE" while the dock mic glows and pulses in the corner has no given reason to associate "that pulsing circle" with "the microphone is actively picking up sound right now" rather than, say, "voice mode is toggled on" (a static/binary state, which is what the pre-existing `.live` class conveyed before tonight's change). The glow is real-amplitude-reactive now, but the button's own icon/label (a mic glyph, tooltip "Toggle listening") still frames it primarily as an **on/off toggle control**, not a **live level meter** — the same element is now serving two different jobs (toggle + meter) with only a subtle radius/opacity change to distinguish "on and quiet" from "on and someone's talking."
- Nothing in the UI (no caption, no legend) says "this pulses with your voice" anywhere near the control. Compare to the Orb, which at least prints a text caption (`say "wake up jarvis"...`, `listening...`, etc.) alongside its visual state.

**Verdict**: reacts correctly and is a genuine improvement over the old fixed-cadence `micpulse` animation (which pulsed identically whether or not anyone was talking, which was actively misleading), but reads as **ambiguous rather than clearly "mic is live"** to someone not told — it's more likely to be perceived as "a slightly fancier version of the existing on/off indicator" than as a real amplitude meter, since it shares a UI slot with the toggle button and has no accompanying label distinguishing the two roles.

### 2.4 Interaction pattern consistency

- **Hub nodes** (GraphCanvas): single click on a leaf selects/loads it (only truly acts on data for Conversations leaves); single click on a hub node expands it. Consistent single-click-to-act pattern.
- **Dock buttons**: single click toggles (graph panel, conversation panel, settings view, mic). Consistent with hub clicking.
- **Chat elements**: message list is click-to-nothing (read-only bubbles) except interactive elements inside them (confirmation Yes/No buttons, source links) — no surprises found.
- **Conversation delete**: click delete icon → PIN modal (not immediate delete) — the one place a second confirmation step exists, and it's the one place that's actually destructive, which is the right call.
- **Settings**: sidebar tab clicks swap panels in place, consistent with the rest of the app's "click = immediate state change, no modal" pattern except where destructive.

No inconsistencies found in this pass beyond what's already flagged in 2.2/2.3 (the mic button's dual toggle/meter role). Loading/error state handling wasn't exhaustively audited across every panel this pass (that would need a dedicated UI test session); spot-checking `ConversationPanel`/`AIProviderSection`/`Topbar` shows try/catch + `console.error` on most async calls with no user-visible error surface (e.g. `Topbar.handlePersonalityClick` silently logs and leaves the UI in the optimistically-updated state even if the backend `updateSettings` call actually failed) — this is a consistent *pattern* (fire-and-forget optimistic updates with console-only error logging), just not a consistent *user-visible* error experience anywhere in the app. Worth a dedicated pass if error visibility matters going forward.

### 2.5 HUD aesthetic consistency

The new `.dock-mic-ring` (cyan border + `box-shadow` glow, `var(--color-cyan)`) matches the existing cyan HUD palette used throughout (`Orb.tsx`'s `cyan = "rgba(100,210,255,...)"`, `Dock.css`'s existing cyan-based `.dock-btn.active` glow). No new colors, fonts, or shapes introduced. One minor deviation: the Dock's mic button/ring still use inline `style={{ position: 'absolute', bottom: '275px' }}` — a magic-number absolute position rather than a flex/grid slot like every other dock button — this predates tonight's change but is worth flagging since it's the one element in the Dock that isn't laid out the same way as its siblings.

---

## PART 3 — CODE QUALITY (Phase 6-specific; not repeating the 08-21 findings that are unchanged)

### 3.1 `personality_mode`/`modifier` in `routes.py` — same drift pattern as before, unchanged

Re-verified: still **no enum/Literal class** exists anywhere in `core/config.py` or `core/models.py` for either value — both are validated inline as string literals in `update_settings_endpoint` (`routes.py:107-114`), silently ignoring invalid values rather than raising. `get_system_prompt(personality_mode, modifier)` is still only called from `/chat` and `/chat/stream` (`routes.py:1304`, `1671`) — **`/voice/input` still does not apply personality/modifier settings at all**, meaning a voice command gets a different (default) system prompt than a typed one even when the user has switched modes. This is exactly the gap the 08-21 audit already flagged (2.4/2.6) and it has not been addressed since — noting it persists rather than re-deriving it.

### 3.2 PIN verification — genuinely hardened server-side, but incompletely wired

The 08-21 audit flagged a **hardcoded PIN "0523" checked client-side** in `PinAuthModal.tsx`. That's fixed: `PinAuthModal.tsx` now contains zero PIN-comparison logic — it's a pure input component that calls `onConfirm(pin)` and lets the caller decide success/failure. `ConversationPanel.handleConfirmDelete` calls `verifyDeletePin(pin)` → `POST /settings/verify-pin` → `routes.py`'s `verify_delete_pin_endpoint`, which compares against `get_setting("conversation_delete_pin", settings.CONVERSATION_DELETE_PIN)` server-side. The PIN value itself never ships to the client. **This is a real fix, not just a relocation of the same bug.**

Two things worth flagging though:

1. **The PIN is still hardcoded as a default** — `config.py:73`: `CONVERSATION_DELETE_PIN: str = "0523"`, the exact same value as before. Moving the *comparison* server-side is real hardening (a user can no longer read the PIN out of the frontend bundle), but the *value* is unchanged and still ships in the repo/config.
2. **No UI exists to ever change it.** `updateSettings()`'s TypeScript signature accepts an optional `conversation_delete_pin` field, and the backend's `POST /settings` handler (`routes.py:115-118`) genuinely supports setting it (validates 4 digits). But grep across the entire frontend finds **zero call sites** that ever populate that field — no settings panel, no UI action, nothing. This is a half-built feature: the plumbing exists end-to-end except the one UI control that would make it usable. Either add that control, or drop the dead `conversation_delete_pin?: string` from the `updateSettings` type until it's wired.

### 3.3 New dead code found this pass

- **`services/jarvis-engine/src/jarvis_engine/api/routes.py:2100`** — `import threading` is now unused inside `speak_and_broadcast()`. This is a leftover from tonight's own "Speaking status" latency fix earlier this session, which replaced the raw-thread approach with `concurrent.futures.ThreadPoolExecutor` + `run_in_executor` but didn't remove the now-orphaned import. Confirmed via `ruff check --select F401`. Small, but real, and self-caused — flagging it honestly rather than omitting it because it's this session's own work.
- **`ruff --select F841`** (unused local variables) surfaced four pre-existing ones, not tied to tonight's changes, not previously called out in the 08-21 audit: `routes.py:174` (`username`, assigned then never read in the automation-detection path), `routes.py:198` and `:1054` (`description`, extracted from action dicts but never used before being passed along/dropped), `routes.py:692` (`query_lower`). None are correctness bugs — all dead reads — but worth a cleanup pass since they suggest half-finished refactors in the automation/browser-command detection code.
- **`main.py:63`**: `from .voice.tts_engine import tts_engine` flagged by ruff as unused — this is a **false positive**, the import is intentionally for its side effect (module import triggers the background Kokoro-loader thread), matching the comment directly above it. Not a real finding, noted so it isn't mistaken for one later.
- **`services/jarvis-engine/tests/test_restart_1.py`, `test_restart_2.py`** — same issue the 08-21 audit already flagged (filenames match pytest's `test_*.py` collection pattern but contain zero `test_*` functions, only a `run_tests()` guarded by `__main__`) — still present, still unfixed. Interesting status change: these were tracked files in the 08-21 snapshot; they now show as **untracked (`??`)** in `git status`, meaning the tracked originals were deleted and untracked copies of the same dead pattern exist in their place. Net effect on the actual problem: unchanged.
- **`services/jarvis-engine/tests/run_live_test.py`** — same shape (manual smoke-test script requiring a live Ollama instance), unchanged from before, correctly still excluded from pytest collection by its filename.

### 3.4 Real, substantial cleanup happened since 08-21 — most of Section 4.2 is now resolved

This is worth stating plainly rather than only listing new problems: comparing current `git status` against the 08-21 audit's dead-code inventory (Section 4.2), **the large majority of it has actually been deleted**:

- ✅ Entire `ai-core/` tree (7 components) — deleted.
- ✅ Entire orphaned secondary chat component tree (`ConversationArea`, `MessageList`, `StreamingMessage`, `ChatComposer`, `ComposerToolbar`, `SendButton`, `MessageAvatar`, `MessageBubble`, `TypingIndicator`) — deleted.
- ✅ `ChatView.old.tsx`/`.old.test.tsx`, `AppHeader.old.tsx`, `AppShell.old.tsx`, `AppMain.tsx`, `OverlayLayer.tsx`, `StatusBar.tsx` — deleted.
- ✅ `usePersonalityStore.ts` (the dead, superseded store) — deleted.
- ✅ `test_foreground.py`, root-level `test_api.py`/`test_dedup.py`/`test_yt.py` — deleted.
- ✅ `update_log.py`, `update_log2.py`, `update_log3.py` — deleted.
- ✅ `diagnose.py` — deleted (confirmed gone from repo root).
- ⚠️ **Not resolved**: `test_restart_1.py`/`test_restart_2.py` (still zero-test files, see 3.3), the nine empty `core/*` stub packages (still present, still empty — `event_bus`, `lifecycle`, `permissions`, `planner`, `router`, `security`, `configuration`, `memory`, `logging`), `cerebras_provider.py` (still correctly, intentionally unwired — not a bug, just still undocumented anywhere outside `manager.py`'s own comment), and the `GraphCanvas`/`RightColumn` duplicate hub-array drift (see 2.1).

Also confirmed fixed since 08-21, outside the dead-code list specifically — **doc drift**: `CLAUDE.md` now correctly documents `uv run python start.py` as the entrypoint (was wrongly `uvicorn --port 8000`), and correctly states the Gemini → OpenRouter → Groq → Ollama provider order (was backwards). The JS-tests-don't-exist claim is also gone from the current `CLAUDE.md`. These three specific drift items from the 08-21 audit's Section 3 are resolved.

### 3.5 Should `PHASE_0_5_ARCHITECTURE_AUDIT.md` be amended or rewritten?

**Recommendation: amend, don't rewrite.** The 08-21 doc is explicitly framed as a dated, point-in-time ground-truth snapshot ("Audited: 2026-08-21"), and the majority of its claims (component graph, store ownership, route inventory, provider architecture, database schema, `core/*` stubs) are re-verified in this pass as **still accurate** — a full rewrite would throw away a correct historical record for no benefit. What's actually needed is narrow: its Section 4.2 dead-code list should get a one-line status update per item (✅ resolved / ⚠️ still open, per 3.4 above), and Section 3's drift items #1 and #4 (run command, provider order) should be marked resolved. Everything else in that document still holds. This document (`PHASE_6_AUDIT.md`) is written as a dated companion rather than an edit to preserve that 08-21 snapshot's integrity — future passes should probably follow the same pattern (new dated file per audit) rather than continuously rewriting one living document, so each snapshot stays trustworthy as "what was true on that date."

---

## Appendix: What this pass did and didn't verify empirically

- **Did measure live**: backend process RAM (`Get-Process` sampling, real running instance, real connected client) over 5 minutes.
- **Did verify by reading code**: `useMicLevelStore.ts` buffer bound, `audio_level_bus.py` drain behavior, all Part 2/3 findings (every file cited above was read in full or grepped and the relevant lines quoted).
- **Did verify by running tools**: `ruff check --select F401,F841` across the full backend package; `tsc --noEmit` / `eslint` (both clean on touched files) from the prior session's work, re-confirmed still clean.
- **Did not do**: live browser devtools heap profiling (no interactive access to the running Tauri webview from this session), a multi-hour RAM soak test (5 minutes was the available window), or exhaustive click-through testing of every panel's loading/error states (spot-checked three; a dedicated UI pass would be needed for full coverage).
