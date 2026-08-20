# JARVIS Codebase Audit — Full Report

**Date:** 2026-08-20
**Scope:** Phases 0-5, full read-through of Voice System, Desktop Automation, Web Search, AI Integration, and Foundation/Desktop UI. Report-only — no fixes applied.

---

## PHASE 5 — Voice System

### `voice/tts_engine.py`

**Issue:** Not true streaming despite the method name `_stream_and_play`.
**Severity:** High
**Root cause:** `async for chunk in communicate.stream(): audio_data += chunk["data"]` accumulates the *entire* audio buffer before writing to disk and calling `pygame.mixer.music.play()`. Playback cannot start until edge-tts finishes synthesizing the whole segment. The FIX-1 "first sentence" split only reduces the size of that first blocking call — it does not remove the blocking behavior itself.
**Direction:** Play audio from an in-memory buffer/pipe as chunks arrive (e.g., feed a pygame `Sound` buffer incrementally, or use `mpv`/`ffplay` piping stdin) instead of waiting for `communicate.stream()` to fully drain.

**Issue:** `pygame.mixer.quit()` + `pygame.mixer.init()` on every single call.
**Severity:** Medium
**Root cause:** Full audio subsystem re-initialization (device open/close) adds ~100–300ms of fixed overhead per utterance, compounding with FIX-1's two-call-per-response pattern (first sentence + rest = 2x this overhead per response).
**Direction:** Initialize the mixer once at engine startup; only call `.stop()`/`.load()`/`.play()` per utterance.

**Issue:** `asyncio.run()` called repeatedly inside a sync method, once per sentence-chunk (FIX 1).
**Severity:** Low
**Root cause:** Every `asyncio.run()` spins up and tears down a new event loop; for a 3-sentence response that's 2 event loop lifecycles just for TTS, plus the overhead is serial (not overlapped) — "generate rest while first plays" in the FIX-1 changelog is aspirational, the actual code still calls the two `asyncio.run()` invocations sequentially, blocking on the first's full playback before generating the second.
**Direction:** Run one event loop for the whole `speak_sync` call; kick off generation of the "rest" concurrently with playback of the first sentence using `asyncio.gather`/`create_task`.

**Issue:** `stop()` fully tears down pygame mixer (`pygame.mixer.quit()`), racing with a concurrent `_stream_and_play()` that's mid-playback on another thread.
**Severity:** Medium
**Root cause:** If `stop()` is called (e.g., wake-word interrupt) while `_stream_and_play` is inside its `while pygame.mixer.music.get_busy()` loop, the mixer object can be destroyed out from under that loop, causing user-space exceptions from pygame (unguarded — the `while` loop's `pygame.mixer.music.get_busy()` call isn't wrapped in try/except).
**Direction:** Guard the polling loop, or use a threading.Event/lock so `stop()` cannot quit the mixer while playback is actively polling it.

**Issue:** `os.unlink(tmp_path)` uses a fixed `time.sleep(0.3)` before delete, and `current_tmp_path` is nulled only inside a `try` that could exit early if unlink itself races with another thread's `speak_sync`.
**Severity:** Low
**Root cause:** Fragile cleanup heuristic (fixed 300ms) rather than confirming the OS file handle from pygame is actually released before delete. On slower disks/AV scanners this can throw `PermissionError`, silently swallowed by the bare `except: pass`.
**Direction:** Track handle release explicitly, or delete temp files in a background sweep rather than immediately post-playback.

---

### `voice/voice_manager.py`

**Issue (root-caused — wake word false triggers during recording):** TOCTOU race between wake-word detection and `is_listening` flag.
**Severity:** Critical
**Root cause:** In `wake_word.py`, the audio callback does `threading.Thread(target=self.on_detected, daemon=True).start()` — but `is_listening = True` is only set *inside* `_on_wake_word_detected`, which runs in that newly spawned thread. Between the moment the wake-word score crosses threshold and the moment the new thread actually executes its first line, the audio callback keeps firing every ~80ms (1280-sample blocks @16kHz) and `get_is_listening()` still returns `False`, so a second (or third) detection thread can spawn for the same utterance. This is the literal cause of "wake word false triggers during recording" — it's not really a false-positive detection, it's a **duplicate dispatch** of a single true detection.
**Direction:** Set `is_listening = True` synchronously inside the audio callback itself (before spawning the thread), guarded by a `threading.Lock`, not inside the spawned thread.

**Issue:** No mic self-echo / feedback suppression.
**Severity:** High
**Root cause:** `wake_word.py`'s level-based interrupt heuristic (`audio_level > 0.08` → stop TTS) has no echo cancellation (`enable_speex_noise_suppression=False`) and no gating on whether the audio is JARVIS's own speaker output leaking into the mic. When "Yes sir?" plays through speakers at any real volume, the mic can pick it up above 0.08 RMS, and if TTS has been "speaking" for >1s (unlikely for "Yes sir?" specifically, but likely for longer LLM responses), `tts_engine.stop()` gets called — JARVIS can self-interrupt its own speech.
**Direction:** Use headphones/AEC, or mute wake-word mic capture (or raise threshold sharply) for the duration `tts_engine.is_speaking` is true, rather than trying to distinguish "user talking over me" from "hearing myself."

**Issue:** `_on_wake_word_detected` now blocks the detection-thread for up to 3s on `t.join(timeout=3)` (FIX 2), then makes a synchronous `requests.post(...)` HTTP call before recording starts.
**Severity:** Medium
**Root cause:** Each of these adds fixed latency onto the "user says wake word → recording actually starts" path, which extends the vulnerable race window described above and delays the moment the mic starts genuinely listening for the command — the user may start talking during the "Yes sir?" TTS and the first ~1-2s of their command gets clipped before `speech_recorder.record()` even opens its stream.
**Direction:** Start `speech_recorder.record()`'s `InputStream` in parallel with the "Yes sir?" playback rather than sequentially after it.

**Issue:** Unbounded thread creation, no cap on concurrent `process_voice` threads if the race above triggers multiple times.
**Severity:** Medium
**Root cause:** Combined with the TOCTOU bug, duplicate `_on_wake_word_detected` invocations each spawn their own `process_voice` thread, each opening a `sd.InputStream` — competing for the same microphone device, which on Windows can silently fail or produce garbled audio for one of them.
**Direction:** Same lock-based fix as above resolves this by construction.

---

### `voice/wake_word.py`

**Issue:** `_audio_callback` re-imports `tts_engine` and does a full attribute-chain lookup on every single audio frame (every 80ms) regardless of whether interrupt logic is even relevant.
**Severity:** Low
**Root cause:** `from .tts_engine import tts_engine` executes on every callback invocation (module is cached so it's cheap, but the `try/except`-wrapped attribute access and `time.time()` call happen continuously even when idle).
**Direction:** Cache the import once in `__init__`; skip the block entirely with an early `if not tts_engine.is_speaking: return` type short-circuit.

**Issue:** No debounce/cooldown after a detection fires — `is_running` stays `True` and the stream keeps calling `self.model.predict(audio)` on every frame even while `on_detected` is executing.
**Severity:** Medium (compounds the Critical race above)
**Root cause:** Only `get_is_listening()` gates re-triggering, and (as noted) it's set too late.
**Direction:** Add a short hard cooldown (e.g., 2s) after any detection, independent of `is_listening`.

---

### `voice/speech_recorder.py`

**Issue:** Fixed silence/energy threshold (`0.01`) with no ambient noise calibration.
**Severity:** Low
**Root cause:** A static RMS threshold will cut recordings short in noisy environments (fans, background music) or fail to detect silence in a very quiet room, leading to either truncated commands or recordings running the full 30s `max_duration`.
**Direction:** Calibrate `silence_threshold` from a brief ambient-noise sample at recorder start.

---

## PHASE 4 — Desktop Automation (`src-tauri/src/lib.rs`)

**Issue:** PowerShell command injection via unsanitized string interpolation.
**Severity:** Critical
**Root cause:** `find_application()` builds PowerShell commands with `format!("Get-StartApps | Where-Object {{$_.Name -like '*{}*'}} ...", app_name)` and similarly for the AppData search — `app_name` is interpolated directly into a single-quoted PowerShell string with **no escaping**. `app_name` originates from LLM-classified voice/chat input (`COMMAND_GENERATION_PROMPT` → `"command"` field), which is itself derived from user text. A crafted utterance like `open app'; Remove-Item C:\Users -Recurse -Force; '` (or anything the LLM faithfully echoes into the `command` field) breaks out of the quoted literal and executes arbitrary PowerShell.
**Direction:** Never interpolate untrusted strings into `-Command` script text. Pass `app_name` as a bound `-ArgumentList` parameter to a parameterized script block, or use `Command::new("powershell").arg("-EncodedCommand")` with a base64-encoded fixed script that reads the argument from `$args[0]`.

**Issue:** `execute_powershell`'s dangerous-command blocklist is trivially bypassable.
**Severity:** High
**Root cause:** Blocklist checks literal substrings (`"remove-item"`, `"del "`, etc.) case-insensitively, but PowerShell has aliases (`ri`, `rd`, `erase`), can be obfuscated (`$e='Rem'+'ove-Item'; & $e ...`), or split across `-Command` invocations. This is a denylist for a Turing-complete scripting language — fundamentally incomplete.
**Direction:** Move to an allowlist model for LLM-generated commands (only permit a fixed set of known-safe cmdlet patterns), or execute generated commands in a constrained/sandboxed PowerShell session (`ConstrainedLanguage` mode).

**Issue:** GPU stats hardcoded (root-caused — GPU stats always 0%).
**Severity:** Medium
**Root cause:** `get_system_info()` returns a static `gpus` array with `"usage": 0, "static": true` — this is a deliberate stub (the `"static": true` flag is a self-documenting marker) left over from removing an `nvidia-smi` call, not an accidental leftover bug. It is, however, **not properly surfaced to the user** — nothing in the frontend appears to check `static: true` and show "N/A" instead of "0%", so the UI likely renders a misleading "0% GPU usage" as if it were live telemetry.
**Direction:** Either wire up a real GPU query (`nvidia-smi --query-gpu=utilization.gpu --format=csv` via `Command`, with WMI fallback for non-NVIDIA), or have the frontend explicitly render "—" / "unavailable" when `static: true` instead of a numeric 0%.

**Issue:** `delete_file`, `shutdown_computer`, `restart_computer` have Rust-side confirmation flags but the confirmation itself is trusted from the caller with no server-side / session-level re-verification.
**Severity:** Medium
**Root cause:** `confirmed: bool` is just a boolean the frontend passes back; anything that can call `invoke("delete_file", {path, confirmed: true})` (e.g., a compromised renderer, or a bug in the UI_ACTION parsing pipeline) bypasses the "ask user" step entirely — the actual gate is in TypeScript (`ConfirmationButtons`), not enforced by Tauri's IPC boundary.
**Direction:** Acceptable for a single-user local desktop app, but worth noting explicitly as a trust boundary — Tauri's IPC surface should be treated as attacker-controlled if any web content is ever loaded (e.g., embedded browser views), which this app does use for foreground search.

---

## PHASE 3 — Web Search

### `tools/web_search.py` / `tools/search_detector.py`

**Issue:** No caching/dedup — identical search queries within a short window re-hit external APIs.
**Severity:** Low
**Root cause:** `search_web()` always calls Tavily/DuckDuckGo fresh; no in-memory or DB-backed cache layer exists despite `memory_manager` already using SQLite.
**Direction:** Cache by normalized query for a few minutes; cheap win for repeated "what's the weather" style queries in a session.

**Issue:** `search_detector.py`'s regex-pattern-list approach for `needs_web_search` is a maintenance and false-positive/negative risk (dead-code-adjacent).
**Severity:** Low
**Root cause:** ~25 hand-maintained regexes (`REALTIME_PATTERNS`) with broad catch-alls like `r'\bwho\s+(?:is|was)\s+[\w\s]+'` will match almost any "who is X" sentence, including ones that are conversational (mitigated only by the separate `CONVERSATIONAL_EXCLUSIONS` list, itself incomplete) — this is inherently brittle pattern-matching doing the job of intent classification.
**Direction:** Not urgent, but flag as a candidate for replacing with a cheap LLM classification call (already paying for one on every automation-eligible message via Groq) instead of two parallel regex/keyword systems.

**Issue:** `search_web`'s Tavily fallback doesn't distinguish "Tavily returned empty results" from "Tavily errored" — both fall through to DuckDuckGo identically, which is fine functionally, but `TavilyClient(api_key=api_key)` is constructed with no timeout, unlike the DDG path which relies on the library's defaults.
**Severity:** Low
**Direction:** Explicit timeout on Tavily client construction/call.

---

## PHASE 2 — AI Integration

### Root cause: Gemini 400 "context too large"

**Severity:** Critical
**Root cause — two compounding bugs:**

1. **Unbounded system-message accumulation in `/chat` and `/chat/stream`.** Every past search result gets saved to the DB as a `role="system"` message (`search_context_note`, routes.py ~1345 and ~1766). On every subsequent turn, `history = await get_conversation_messages(conversation_id)` pulls **all** of them, and `search_context_accumulated = "\n\n" + "\n".join(m.content for m in system_msgs)` concatenates **every system message ever saved for that conversation, uncapped**, into the new system prompt. The only truncation anywhere (`search_context[:1500]`) applies solely to the *current* turn's fresh search results before they're saved — not to the accumulated total. A conversation with 5 web searches over its lifetime permanently carries all 5 search-result blocks in every future request's context, growing linearly and unboundedly.
2. **Gemini-specific message loss compounds this.** `GeminiProvider._format_messages()` has its own truncation (`other_msgs[-10:]` when `len(messages) > 20`) but this is a *message-count* cap, not a token-count cap — 10 long messages (each potentially containing a 1500-char search block) can still overflow Gemini's request-size limits. Separately, this method does `for m in messages: if m.role == "system": continue` — this drops **every** system-role message except the one designated `system_msg` (found via `next(...)`, i.e. only the *first* system message in the list). Since `full_messages` contains multiple system messages (main prompt, memory context folded into it, `ui_reminder`, automation context, search context — several of these are separate `Message(role="system", ...)` entries inserted via `full_messages.insert(-1, ...)`), Gemini silently receives **only the first one** and loses automation/search instructions that were correctly sent to Ollama/Groq/OpenRouter. This is a functional bug independent of the size issue, and it means Gemini's "context too large" errors are hit by a payload that, ironically, still doesn't contain everything intended.

**No token counting exists anywhere in the codebase** (confirmed — no tiktoken, no character-based estimate correlated to model limits, nothing).

**Direction:**
- Cap `search_context_accumulated` the same way the per-turn search context is capped (e.g., keep only the N most recent search notes, or drop them from history replay entirely — they were already used to answer their originating turn).
- Fix `_format_messages` to fold *all* system-role messages into the single `system_instruction` (concatenated), not just the first found — this both fixes the data-loss bug and, combined with the accumulation cap above, keeps the payload bounded.
- Add a real token-budget check (rough `len(text)//4` heuristic is enough) before sending to any provider, trimming oldest history first.

---

### `providers/groq_provider.py`

**Issue:** Duplicated retry logic between `chat()` and `stream()`, and the fallback retry re-uses `groq_messages`/`client` from the `try` block inside the `except` — fragile but not currently broken, since both are assigned before the only call that can raise. Flagging as a latent `NameError` risk if `Groq(api_key=...)` itself ever raises (e.g., malformed key) before `groq_messages` is built.
**Severity:** Low
**Direction:** Wrap client construction separately, or restructure retry as a small helper function taking `model` as a parameter instead of duplicating the whole `try/except` body twice per method.

**Issue:** Fallback model `"llama-3.1-8b-instant"` is hardcoded in two places (chat + stream) rather than in config.
**Severity:** Low
**Direction:** Move to `settings.GROQ_FALLBACK_MODEL`.

### `providers/manager.py`

**Issue:** `set_active_provider` reorders the in-memory `providers` list, which is a **global singleton** (`provider_manager = ProviderManager()`), so "switch provider" from the UI mutates process-wide state shared across all conversations/users of this single-user app. Fine for a single-user desktop app, but worth noting: it's not per-conversation or per-request state, so if two chat requests are in-flight concurrently (e.g., a stream + a background automation classification), a provider switch mid-flight changes the ordering the second request sees, non-deterministically.
**Severity:** Low (single-user context limits blast radius)
**Direction:** Not urgent; document the singleton assumption.

### `memory/memory_manager.py`

**Issue:** `get_relevant_memories` builds a SQL query with `" OR ".join(["LOWER(content) LIKE ?" for _ in words])` — parameterized correctly (no injection), but for a query with many words this becomes a large OR-chain doing full table scans (`LIKE '%word%'` defeats any index) on every chat turn.
**Severity:** Low (dataset likely small for single-user local app, but will degrade over time)
**Direction:** FTS5 virtual table for `memories.content` would make this both faster and more relevant (currently pure substring OR-matching has no ranking beyond `importance`/`last_accessed`).

**Issue:** `extract_and_save_memories` trigger-word matching (`"i am "`, `"i use"`, etc.) will false-positive constantly — e.g., "i am not sure if..." gets saved as a `personal` memory with importance 8, "how do i use the graph feature" gets saved as a `fact` memory. No LLM-based extraction, just substring matching on a fixed English phrase list.
**Severity:** Medium (data-quality issue, pollutes the memory store the assistant relies on for personalization)
**Direction:** This is doing real semantic work (fact extraction) with a keyword heuristic — worth an LLM-based extraction pass (even a cheap Groq call) given how much downstream behavior (`get_relevant_memories` injected into every system prompt) depends on memory quality.

---

## PHASE 0-1 — Foundation + Desktop UI

### Root cause: conversation shows in wrong context after voice

**Severity:** High
**Root cause — two issues:**

1. **`useJarvisChat.ts`'s `connectVoiceWebSocket` `useEffect` has no cleanup function** — it opens a `WebSocket` but never calls `.close()` on unmount, and `connectVoiceWebSocket`'s own `onclose` handler auto-reconnects recursively. In React 18 StrictMode (dev) this effect runs twice, opening two live sockets, each with its own closure over `addMessage`/`setStatus` — leading to duplicate `voice_input`/`voice_response` messages appended to the chat, or handlers firing against stale state.
2. **Backend event ordering race in `routes.py` + `voice_manager.py` + `main.py`.** Trace the actual sequence for a voice command:
   - `voice_manager.process_voice()` transcribes, then calls `self.on_transcription(text, direct_result)` — in `main.py` this **fires a background thread and returns immediately** (`t = threading.Thread(target=speak_and_broadcast); t.start()` — no `.join()`).
   - `process_voice()`'s `finally` block runs essentially immediately after, POSTing `{"status": "idle"}` to `/voice/status/update`.
   - Meanwhile the background thread from `main.py` is still making its (potentially multi-second) HTTP call to `/voice/input`, which itself broadcasts `"processing"` → `"voice_input"` → `"voice_response"`.
   - **Net effect:** the WebSocket can emit `listening → idle → processing → voice_input → voice_response → speaking → idle`, i.e. `idle` fires *before* `processing`, causing the orb/UI to flash back to idle mid-pipeline, then jump back into "processing/speaking" — visibly inconsistent state, and if a chat message renders while status says `idle`, it can appear disconnected from the "conversation in progress" context the user just experienced.
   - There is no request ID / sequence number on any broadcast event, so the frontend has no way to detect or discard stale/reordered events even if it wanted to.

**Direction:**
- Add cleanup (`return () => voiceSocket?.close()`) to the `useEffect` in `useJarvisChat.ts`, and guard against duplicate connections (module-level singleton check, which partially exists via `let voiceSocket` but doesn't prevent overlapping connects).
- Make `voice_manager.py`'s idle-status POST wait for (or be triggered by) actual completion of the `/voice/input` round trip, not fire independently right after transcription. Simplest fix: have `/voice/input`'s handler itself broadcast the final `idle` status once it's fully done (it already broadcasts `voice_response`), and remove the redundant idle-POST from `voice_manager.py`'s `finally` block entirely — right now there are two independent idle-status sources racing.

### `stores/useAIStore.ts`, `useConversationStore.ts`, `useAppStore.ts`

**Issue:** `showActionFeedback`/`setInspectorMessage` in `useAppStore.ts` store timers on `window` (`(window as any)._feedbackTimer`) instead of component/store-local state.
**Severity:** Low
**Root cause:** Works, but breaks encapsulation and is fragile if two different code paths call `showActionFeedback` in quick succession from different contexts — acceptable given it's explicitly clearing/resetting the same global timer, but it's a code smell worth flagging as dead-simple to fix.
**Direction:** Use a module-level `let` instead of `window` global.

**Issue:** No unused imports/dead code found in the three stores — clean.

### `Orb.tsx`

**Issue:** Full canvas redraw loop (`requestAnimationFrame`) runs continuously whenever `graphMode === "3d"`, drawing ~30+ discrete shapes/arcs/particles every frame, even when `effectiveStatus === "idle"` and nothing is visually changing except the ambient rotation.
**Severity:** Low
**Root cause:** No frame-skipping/throttling for idle state in 3D mode (the 2D-mode optimization at the bottom of the file explicitly exists — `hasDrawn2D` check — but no equivalent "idle 3D" throttle). Continuous 60fps canvas redraws for a decorative always-visible element is a real, measurable CPU/GPU cost on a background-running desktop app.
**Direction:** Reduce to ~15-20fps when `effectiveStatus === "idle"` and `graphMode === "3d"`, since idle animation is purely ambient (slow rotation) and doesn't need 60fps smoothness.

**Issue:** `getCaption()` and the `statusText`/`statusColor` object-literal lookups are recreated on every render (new object allocated each render) rather than hoisted as module constants.
**Severity:** Low (negligible in practice, but easy fix)
**Direction:** Hoist `statusText`/`statusColor` maps outside the component.

---

## Prioritized Top 10 (user impact × fix effort)

| # | Issue | Phase | Severity | Effort | Why it's here |
|---|-------|-------|----------|--------|----------------|
| 1 | Unbounded system-message/search-context accumulation causing Gemini 400s | 2 | Critical | Low | Directly breaks a whole provider on any conversation with a few searches; fix is a small cap/slice, not a redesign |
| 2 | PowerShell command injection via `app_name` in `find_application`/Rust `format!` | 4 | Critical | Medium | Remote-code-execution-adjacent from voice/chat input; fix is parameterization, contained to 2 functions |
| 3 | Wake-word TOCTOU race spawning duplicate detection/recording threads | 5 | Critical | Low | Root cause of the reported "false triggers"; fix is a lock + earlier flag-set, a few lines |
| 4 | WebSocket event ordering race (`idle` before `processing`) causing UI/context desync | 0-1 / 2 | High | Medium | Directly matches reported symptom; fix requires consolidating two independent status-broadcast sources into one |
| 5 | Gemini `_format_messages` drops all but the first system message | 2 | High | Low | Silent data loss — Gemini answers without search/automation instructions other providers get; a loop-fix |
| 6 | `_stream_and_play` isn't actually streaming (root cause of remaining TTS delay) | 5 | High | Medium-High | Explains why FIX-1's sentence-split only partially helped; real fix needs incremental playback |
| 7 | No mic echo/self-interrupt guard for TTS | 5 | High | Medium | Causes JARVIS to potentially cut off its own speech; needs threshold/mute-while-speaking logic |
| 8 | Missing `useEffect` cleanup on voice WebSocket (duplicate connections) | 0-1 | Medium | Low | Classic React bug, single-line fix, but causes duplicate messages/stale handlers |
| 9 | Memory extraction via naive keyword triggers pollutes long-term memory | 2 | Medium | Medium | Degrades personalization quality silently over time; every future prompt carries the noise |
| 10 | Blocklist-based PowerShell safety check is bypassable | 4 | High | Medium-High | Real security gap, but full fix (sandboxing/allowlist) is a bigger lift than #2, hence ranked below it |

---

**Report only — no fixes applied.** See `docs/CLEANUP_REPORT.md` for the separate dependency/dead-file cleanup analysis.
