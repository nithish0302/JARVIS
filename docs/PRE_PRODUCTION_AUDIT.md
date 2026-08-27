# JARVIS — Pre-Production Audit (Phases 6–9)

**Date:** 2026-08-27
**Scope:** `services/jarvis-engine/` + `apps/desktop/` at `main` @ `a4aa25dd`
**Method:** mirrors `docs/PHASE_0_5_ARCHITECTURE_AUDIT.md`. Findings only — no code was changed.

---

## Verdict

**Not production-ready.** Four Critical issues block release. Two are credential
exposure in version control, one is a real destructive-action bypass reachable
by voice, and one makes the backend test suite unusable as a release gate.

The recurring "works in chat, silently missing in voice" bug class is **still
present and is now a security issue, not just a functional one** — see C1.

| Severity | Count |
|---|---|
| Critical | 4 |
| High | 6 |
| Medium | 9 |
| Low | 8 |

---

## CRITICAL — blocking production

### C1. Voice path performs destructive actions with no confirmation

The single most important finding. Same bug class as before; this time it
bypasses the safety system rather than a feature.

`enforce_destructive_confirmation()` is the *only* real enforcement point
(prompt text is advisory). It is called from exactly two places:

| Path | Line | Calls enforcement? |
|---|---|---|
| `/chat` | `routes.py:2178` | yes |
| `/chat/stream` | `routes.py:2735` | yes |
| `/voice/input` | `routes.py:281–627` | **no** |

The frontend voice handler applies a client-side filter, but it covers only two
actions (`useJarvisChat.ts:104–108`):

```ts
const VOICE_EXCLUDED_ACTIONS = new Set(["delete_conversation", "delete_file"])
```

Meanwhile `uiActionExecutor.ts` executes these **immediately, with no gate**:

- `send_email` — `uiActionExecutor.ts:538`
- `create_event` — `uiActionExecutor.ts:594`
- `create_github_issue` — `uiActionExecutor.ts:714`

Those raw cases are safe in chat *only because* the backend rewrote the tag to
`confirm_action:*` first. Voice never does that rewrite.

**Failure scenario:** with Gmail connected, the user says *"email Sarah and tell
her I'm quitting."* The LLM emits `[UI_ACTION:send_email:sarah@x.com:Re:...]`.
`/voice/input` returns it untouched → the voice filter allows it →
`executeUIActions` calls `api.sendEmail(...)`. The email is sent. No
confirmation, no undo. Misrecognized speech triggers it just as easily.

`delete_file` is currently safe from voice, but by the client-side list only —
delete one line from that `Set` and the backend has nothing behind it.

**Fix direction:** call `enforce_destructive_confirmation()` in `/voice/input`
before broadcasting, and derive the voice exclusion list from one shared
constant rather than a hand-maintained literal.

---

### C2. Git-tracked SQLite database containing live Google OAuth tokens

```
services/jarvis-engine/src/data/jarvis.db              ← TRACKED
services/jarvis-engine/src/data/chroma/chroma.sqlite3  ← TRACKED
```

Contents of the tracked DB:

```
plugin_credentials: 2 rows
  plugin='google'  key='access_token'   blob=242 bytes  created 2026-08-26T08:36:01Z
  plugin='google'  key='refresh_token'  blob=242 bytes  created 2026-08-26T08:36:01Z
```

Added in commit `a8908af9` ("bug fixed"). Also carries `conversations`,
`messages`, `memories`, and `settings` tables.

**Root cause:** `.gitignore` excludes `services/jarvis-engine/data/` — the real
runtime path — but **not** `services/jarvis-engine/src/data/`. That second tree
is created whenever the engine is started with cwd = `src/`, because `DB_PATH`
is the relative `"data/jarvis.db"` (`config.py:49`).

The blobs are DPAPI-encrypted (user-scoped), so they are not trivially readable
off-machine — but a refresh token in version control is a credential artifact
regardless, and refresh tokens do not expire on their own.

**Fix direction:** `git rm --cached` both files, add `**/data/` to `.gitignore`,
revoke the Google grant, re-authorize. Purging history is optional here given
DPAPI scoping — revocation is not.

---

### C3. Live Tavily API key permanently in git history

```
commit f93e9f34  "PHASE 3-milestone 4 is completed feat:ui action"  2026-08-15
  + services/jarvis-engine/.env
      TAVILY_API_KEY=tvly-<58 chars>
      SEARCH_PROVIDER='tavily'
```

Removed from tracking later in `49a6edbf` ("Remove .env from tracking"), and
`.env` is correctly ignored today — but the blob is still reachable at that
commit and would ship with any clone, fork, or public push.

**Deleting the file did not revoke the key. It must be rotated.**

---

### C4. Full backend test suite segfaults

```
$ uv run pytest tests/
........................................ [ 88%]
.....Windows fatal exception: access violation
exit 139
```

Not flakiness — a hard crash, reproducible.

```
Thread 0x00001abc:
  wake_word.py:132 in __init__
  voice_manager.py:426 in _load_wake_word     ← still initializing
Thread 0x00003624:
  voice_manager.py:895 in shutdown            ← tearing down concurrently
  main.py:201 in lifespan
```

The session-scoped `TestClient(app)` fixture (`conftest.py`) runs the app's
**real** lifespan, which boots the actual voice subsystem. At teardown,
`voice_manager.shutdown()` races the wake-word loader thread that is still
constructing → access violation.

A second thread shows the suite reaching out to the network:

```
faster_whisper/utils.py:116 download_model
  huggingface_hub/_snapshot_download.py:165 snapshot_download
```

Tests download Whisper weights from HuggingFace. That makes them
network-dependent and slow, and it widens the race window.

**Actual counts, run file-by-file:**

| Result | Count |
|---|---|
| Passed | **162** |
| Failed | 0 |
| Files collecting zero tests | 2 (`test_restart_1.py`, `test_restart_2.py`) |

No genuine assertion failures. The code under test is fine; the harness is not.
As it stands the suite cannot gate a release — CI would be red or nondeterministic.

**Fix direction:** stub the voice subsystem in the test lifespan (or gate it
behind an env flag `conftest` sets), and have `shutdown()` join the loader
threads before releasing native handles.

---

## HIGH

### H1. `create_github_issue` confirmation is a dead end — the action never runs

`enforce_destructive_confirmation()` rewrites the tag to
`confirm_action:create_github_issue:...` (`routes.py:1324`). The user then
confirms. But the confirmation dispatcher in `useJarvisChat.ts:177–285` only
branches on:

- `delete_file` (line 181)
- `send_email` (line 219)
- `create_event` (line 246)

`create_github_issue` falls through to the `else` at line 274:

```ts
content: `Command confirmation received.`
setPendingCommand(null)
```

The user is told it worked. **No issue is created.** Silent failure — and the
backend guard is what routes it into this dead branch, so the safety fix
introduced the functional break.

### H2. GitHub plugin interpolates unencoded input into API URLs

`github_plugin.py` builds every URL by f-string with no `urllib.parse.quote`:

```python
list_issues:        f"{BASE}/repos/{repo}/issues?state={state}&per_page=100"   # :57
search_issues:      f"{BASE}/search/issues?q={query}"                          # :74
list_pull_requests: f"{BASE}/repos/{repo}/pulls?state={state}..."              # :99
get_pr_status:      f"{BASE}/repos/{repo}/pulls/{pr_number}"                   # :113
search_code:        f"{BASE}/search/code?q={q}"                                # :140
```

`repo`, `state`, and `query` arrive from LLM-generated `UI_ACTION` payloads.
A `repo` value containing `../`, `?`, or `#` reaches unintended API paths
carrying the user's token. Exposure is bounded to `api.github.com` (httpx does
not follow redirects by default, so the token cannot be steered off-host), which
is why this is High rather than Critical — but it is unvalidated input in a URL.

### H3. Rust `delete_file` has no path allowlist and deletes directories recursively

`apps/desktop/src-tauri/src/lib.rs:723`

```rust
fn delete_file(path: String, confirmed: bool) -> Result<String, String> {
  if !confirmed { return Err(...) }
  ...
  let result = if is_dir { fs::remove_dir_all(&path) } else { fs::remove_file(&path) };
```

`confirmed` is supplied by the caller (`deleteFile(cmdPayload, true)`), so it is
plumbing, not enforcement. There is no denylist for system paths and no depth
limit. `delete_file:C:\Windows` would proceed. The only thing standing in front
of it is the LLM plus one UI confirmation.

### H4. Provider API keys stored in plaintext; plugin credentials are not

Two different standards in the same codebase:

- Plugin credentials → DPAPI-encrypted (`credential_store.py`) ✔
- Provider API keys → raw string into the `settings` table (`routes.py:252–270`)

```python
val = str(request["gemini_api_key"]).strip()
await set_setting("GEMINI_API_KEY", val)   # plaintext
```

This compounds C2: if the engine is ever started with cwd = `src/`, those
plaintext keys land in the git-tracked database.

### H5. No authentication on any endpoint

CORS is correctly restricted (`main.py:211`, `allow_origins=["http://localhost:1420"]`),
which stops browsers — but CORS is not authentication. Any local process can
call the API directly:

- `POST /plugins/gmail/send` — send mail as the user
- `PUT /settings/provider-config` — overwrite API keys
- `GET /plugins/github/repos` — read repo data
- `DELETE /memories/{id}` — (PIN-gated, see H6)

Only `delete_conversation` and `delete_memory` have any gate at all.

### H6. Delete PIN is brute-forceable and stored in plaintext

`routes.py:150` exposes an unauthenticated oracle:

```python
@router.post("/settings/verify-pin")
async def verify_delete_pin_endpoint(request: dict):
    return {"valid": pin == stored_pin}
```

- 4 digits, numeric only (`routes.py:167`) → 10,000 combinations
- No rate limit, no lockout, no attempt log
- Stored plaintext in `settings`
- Non-constant-time comparison

The PIN checks themselves are correctly **server-side** on both delete endpoints
(`routes.py:2910`, `routes.py:2996`) — that part is right and tested. The
weakness is the secret, not its placement.

---

## MEDIUM

### M1. `/chat` capabilities still absent from `/voice/input`

Systematic comparison of the three handlers:

| Capability | `/chat` | `/chat/stream` | `/voice/input` |
|---|:---:|:---:|:---:|
| Personality mode / modifier | ✔ | ✔ | ✔ |
| Plugin capabilities (via `get_system_prompt`) | ✔ | ✔ | ✔ |
| Web search | ✔ | ✔ | ✔ |
| Provider fallback cascade | ✔ | ✔ | ✔ |
| Fallback notification | ✔ | ✔ | ✔ |
| Daily briefing | ✔ | ✔ | ✔ |
| **Destructive-action enforcement** | ✔ | ✔ | ✘ *(C1)* |
| **Relevant-memory context** | ✔ | ✔ | ✘ |
| **`UI_ACTION_REMINDER`** | ✔ | ✔ | ✘ |
| **`SYSTEM_STATE` block** | ✔ | ✔ | ✘ |
| **`UI_ACTION_INSTRUCTION` when automation fires** | ✔ | ✔ | ✘ |
| **Conversation persistence** | ✔ | ✔ | ✘ |
| **Memory extraction** | ✔ | ✔ | ✘ |
| **Gap logging** | ✔ | ✔ | ✘ |

Personality/search/plugin parity — the three the task asked about — is genuinely
fixed and holds. The remaining gaps are the ones above.

Note the `if/else` at `routes.py:~440`: when voice detects automation, the whole
`UI_ACTION_INSTRUCTION` block is dropped. `/chat` inserts automation context as
an *extra* message and keeps the instruction. Same shape as the earlier
truncation bug the file's own comment warns about.

### M2. `search_performed` means different things in `/chat` vs `/chat/stream`

- `/chat` — set `True` only when results actually came back (`routes.py:2104`)
- `/chat/stream` — meta chunk sends `search_needed`, the *intent* (`routes.py:2507`)

A search that times out reports `search_performed: true` on the stream path and
`false` on the chat path. `routes.py:2235` sets a `search_performed` local that
is then never read (ruff `F841`) — the leftover of the divergence.

### M3. `routes.py` should be split before production — yes, it has grown

It has grown **+87% since Phase 4**, and by ~330 lines since the last check:

| Lines | Commit |
|---|---|
| 1770 | phase 4 milestone 4 files operation |
| 2165 | Fixed bug and improving the application |
| 2657 | phase 6 completed |
| 2877 | phase 7 bug fixed |
| 2972 | Phase 8 M0: Plugin system foundation |
| 3121 | Phase 8 M5: Weather plugin |
| **3300** | **HEAD** |

Measured duplication between the two largest handlers:

```
/chat body (code only):              313 lines
/chat/stream body:                   527 lines
identical non-trivial shared lines:  118
```

Every bug in C1/M1/M2 is a *drift* bug — the same logic maintained in two or
three places and updated in only one. The proposed split
(`routes/chat.py`, `routes/voice.py`, `routes/plugins.py`, `routes/settings.py`)
is warranted, but on its own it would only move the duplication into four files.
The higher-value refactor is extracting the shared request pipeline — prompt
assembly, search, cascade, post-processing — into one module all three handlers
call, so "add it to chat, forget voice" stops being possible. Split second.

### M4. Orphaned UI actions in both directions

Declared to the LLM, **no** handler in `uiActionExecutor.ts`:

- `spotify_play`, `spotify_pause`, `whatsapp_send` (`placeholders.py:28,36`)

Currently unreachable — `registry.is_configured()` is false for both and no
endpoint exists to store their credentials — so they never enter the prompt
today. If either is ever wired up they become silent no-ops.

Handled in the frontend, **never** emitted by the backend:

- `switch_provider` (`uiActionExecutor.ts:167`, `:839`) — dead branch.

`[UI_ACTION:tag]` in the prompt text is a literal placeholder, not an action.

### M5. GitHub actions advertised even when GitHub is not connected

GitHub is documented in **two** places: the always-on `SYSTEM_CAPABILITIES`
block (`routes.py:930–936`) and the conditional plugin registry. Every other
plugin uses only the registry, which correctly hides itself when unconfigured.
Result: with GitHub disconnected the model still offers GitHub actions, emits
the tag, and the user gets a `503` from `_check_plugin`.

### M6. No test coverage on the security-critical surface

Test files referencing each subject:

| Subject | Files |
|---|---|
| `enforce_destructive_confirmation` | **0** |
| `credential_store` / `store_credential` | **0** |
| Gmail plugin | **0** |
| Calendar plugin | **0** |
| GitHub plugin | **0** |
| `provider-config` endpoint | **0** |
| `send_email` / `create_event` / `delete_file` | **0** |
| `is_destructive_action` | **0** |

162 tests exist and voice/wake-word/continuous-mode coverage is genuinely strong
(~60% of the suite). PIN-gated deletes are properly tested
(`test_conversation_delete_pin.py`, `test_memory_crud.py`). But the entire
plugin layer and the entire destructive-action guard have **zero** tests — which
is precisely why C1 and H1 went unnoticed.

Given risk, these deserve tests first:

1. `enforce_destructive_confirmation()` — one test per action, plus a test
   asserting `/voice/input` applies it (would have caught C1)
2. The confirm → execute round trip for all four actions (would have caught H1)
3. `credential_store` encrypt/decrypt/delete round trip

### M7. Google access token sent in a URL query string

`google_auth.py:78`

```python
f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}"
```

Query strings land in proxy logs, crash reports, and local HTTP debug output.
Google's tokeninfo accepts this form, but a header or POST body is the safer
carrier.

### M8. Two frontend test failures

```
Test Files  2 failed | 31 passed (33)
     Tests  2 failed | 75 passed (77)
```

Both are real, neither is flaky:

1. **`Dock.test.tsx`** — asserts 3 buttons; `Dock.tsx` renders **5**
   (lines 17, 31, 43, 60, 75). Stale test left behind by a UI change.
2. **`Orb.tsx:103`** — jsdom returns `null` from `getContext("2d")`;
   `ctx.setTransform(...)` is called unguarded and throws. A missing-canvas
   guard would fix both the test and any real environment without 2D canvas.

### M9. Unconditional debug output; `[SAFETY]` lines log action payloads

No `DIAG`-style instrumentation was found — that earlier debugging is clean.
But **45+ bare `print()` calls in `routes.py` alone**, none behind a debug flag:
`[VOICE INPUT ENDPOINT]`, `[CHAT]`, `[STREAM]`, `[SAFETY]`, `[BRIEFING]`.

Two log user content rather than metadata:

```python
routes.py:1310         print(f"[SAFETY] Blocked unconfirmed send_email UI_ACTION for '{payload}' ...")
memory_manager.py:401  print(f"[MEMORY EXTRACTED] ... Content: {content}")
```

`payload` is recipient + subject + body. No API key, token, or PIN is printed
anywhere — that check passes — but email bodies and extracted personal memories
go to stdout unconditionally.

---

## LOW

- **L1.** Dead code (ruff, isolated): 9 unused imports (`F401`) in `main.py`,
  `credential_store.py`, `google_auth.py`, `cerebras_provider.py`,
  `gemini_provider.py`, `openrouter.py`, `speech_recorder.py`, `wake_word.py` ×2;
  3 unused locals (`F841`) at `routes.py:2235`, `memory_manager.py:394`,
  `cerebras_provider.py:50`; 3 bare `except` (`E722`) at `routes.py:635,649,2864`.
- **L2.** Stale duplicate trees: `services/jarvis-engine/services/jarvis-engine/src/.../tts_engine.py`
  (a nested copy of the tree) and the root `jarvis/` directory (an unused Tauri
  scaffold duplicating `apps/desktop`).
- **L3.** `tests/test_restart_1.py` and `test_restart_2.py` collect zero tests —
  manual scripts under `if __name__ == "__main__"`. They inflate the file count
  and collect nothing.
- **L4.** `PluginSection.tsx` hardcodes `http://localhost:8765` (lines 20, 38, 59, 78)
  instead of importing `JARVIS_ENGINE_URL`, and uses a blocking `alert()` at line 51.
- **L5.** `JarvisSettings` (`jarvisApi.ts:549`) omits `preferred_provider` and
  `preferred_model`, both returned by `GET /settings` (`routes.py:137–138`).
- **L6.** Every plugin client function is typed `Promise<any>` / `Promise<any[]>` —
  Gmail, Calendar, GitHub, Weather. The types don't *mismatch* the API; they're
  absent. `tsc --noEmit` passes clean, but it has nothing to check.
- **L7.** `credential_store.delete_credential()` and `list_credential_keys()`
  skip the `_check_windows()` guard the other two functions call.
- **L8.** 13 `console.log` calls on production frontend paths.

---

## What passed

Worth recording — these were checked and are correct:

- **No credential is ever logged, printed, or returned in a GET response.**
  `GET /settings` returns `*_configured` booleans only, never key values
  (`routes.py:120–147`). `GET /plugins` returns `is_configured` only. The Google
  callback returns HTML with no token. No `print()` anywhere emits a key, token,
  or PIN. *(Part 2.1 — clean.)*
- **No shell string interpolation anywhere.** The new plugins (GitHub, provider
  config) are pure `httpx` and touch no shell. Every PowerShell call in
  `lib.rs` is either `-File script.ps1` with `.arg()`-parameterized input
  (`lib.rs:137`) or a fixed zero-parameter `-Command` (`lib.rs:257`).
  `taskkill` uses `.args([...])`. *(Part 2.3 — clean.)*
- **PIN checks are genuinely server-side** on both delete endpoints, not
  client-side comparisons — and both are tested.
- **Plugin credentials use DPAPI**, with parameterized SQL throughout
  `credential_store.py`.
- **`.env` is correctly ignored today**, and CORS is properly restricted to the
  Vite dev origin.
- **`tsc --noEmit` passes with zero errors.**
- **Personality mode, web search, and plugin capabilities are now genuinely
  identical across `/chat` and `/voice/input`** — the parity work held. The
  remaining voice gaps are listed in M1.

---

## Recommended order

**Before production:**

1. C1 — call `enforce_destructive_confirmation()` in `/voice/input`
2. C2 — untrack `src/data/`, fix `.gitignore`, revoke + re-authorize Google
3. C3 — rotate the Tavily key
4. C4 — stub the voice subsystem in tests; make the suite green as one run
5. H1 — add the `create_github_issue` confirmation branch

**Immediately after:**

6. H4, H6 — encrypt provider keys; strengthen or replace the 4-digit PIN
7. H2, H3 — URL-encode GitHub inputs; add a path denylist to `delete_file`
8. M6 — tests for the destructive-action guard and the confirm round trip

**Then:** M1 (close the remaining voice gaps), M3 (extract the shared pipeline,
*then* split the file), and the Low-severity cleanup.
