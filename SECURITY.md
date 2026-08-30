JARVIS is a single-user desktop app that runs entirely on your own
machine. This document explains what it stores, what leaves your
machine and where, what's gated behind confirmation, and one deliberate,
accepted gap.

## Credential storage

Two different kinds of secret, both encrypted, both Windows DPAPI:

- **Plugin OAuth tokens** (Gmail/Calendar's Google access + refresh
  tokens, GitHub's fine-grained PAT) — stored via
  `services/jarvis-engine/src/jarvis_engine/plugins/credential_store.py`,
  encrypted with `CryptProtectData` (Windows DPAPI, scoped to your
  Windows user account) before ever touching disk.
- **AI provider API keys** (Gemini/Groq/OpenRouter, saved via
  Settings > Providers) — go through the same `store_credential()` /
  DPAPI path, not a plaintext `.env`-style write. On first boot after
  this fix, JARVIS also self-heals any older install that had written a
  plaintext key: it reads the legacy value once, re-writes it through the
  encrypted path, and deletes the plaintext row.

Nothing is ever stored plaintext in the SQLite database. Because DPAPI
keys are scoped to your Windows user account, the encrypted blobs are
only decryptable by that same account on that same machine — copying
`jarvis.db` to another machine or user account does not hand over usable
credentials.

`GET /settings` and `GET /plugins` only ever return `*_configured`
booleans, never the underlying key/token values — nothing prints,
returns, or logs a live credential.

## What stays local vs. what leaves your machine

**Sent to external services, by design:**

- Whichever AI provider is active (Gemini, Groq, OpenRouter, or your own
  Ollama instance) receives the text of your messages/conversation
  context to generate a response. If web search is enabled, your search
  query goes to Tavily (if configured) or DuckDuckGo (the default
  fallback, no key required).
- Connected plugins send requests to their respective providers: Gmail
  and Calendar actions go to Google's APIs (using your own OAuth grant);
  GitHub actions go to `api.github.com` (using your own PAT); Weather
  queries go to Open-Meteo (no auth, no account needed).

**Stays local:**
- Conversation history, extracted long-term memories, and settings live
  in a local SQLite database (`services/jarvis-engine/data/jarvis.db`)
  and a local ChromaDB vector store — neither is synced anywhere.
- Voice audio is processed locally (Whisper transcription, wake-word
  detection, Kokoro TTS) — raw audio is not sent to a cloud speech API.
- Credentials, per above, never leave the machine in decryptable form.

If you connect a plugin, you are explicitly opting that plugin's traffic
(and only that plugin's) into talking to its provider. Disconnecting a
plugin (Settings > Plugins > Disconnect) deletes its stored credentials
immediately.

## Destructive-action confirmation gate

Four actions are treated as destructive and require an explicit
confirmation step before they run, regardless of whether they were
triggered by chat, voice, or the LLM's own free-form output:

- `delete_file`
- `send_email`
- `create_event`
- `create_github_issue`

This is enforced by `enforce_destructive_confirmation()` in
`services/jarvis-engine/src/jarvis_engine/api/routes.py`, called at every
request-handling path that can produce user-facing text (`/chat`,
`/chat/stream`, `/voice/input`). It rewrites any raw, unconfirmed
`[UI_ACTION:<destructive-action>:...]` tag — however it was produced,
including a hallucinated one — into a `confirm_action` tag instead, which
requires the user to explicitly confirm before the frontend will execute
it. This is a genuine server-side gate: the model being told "ask for
confirmation" in its system prompt is advisory and can be ignored by the
model; this rewrite cannot be, because it happens after generation, on
every path, unconditionally.

`delete_file` additionally enforces a path safety check independent of
confirmation: it rejects deleting drive roots, `C:\Windows`, `C:\Users`,
your home directory root, or any path shallower than a small minimum
depth — confirmation alone doesn't make an accidental `C:\` delete safe.

## Delete-PIN system

Deleting a conversation or a memory additionally requires a 4-digit PIN
(default `0523`, changeable in settings) on top of the destructive-action
gate above. The PIN itself:

- Is hashed with **PBKDF2-HMAC-SHA256, 260,000 iterations, random salt**
  — never stored or compared in plaintext.
- Is checked with a **constant-time comparison**.
- Is **rate-limited**: 5 failed attempts within a rolling window trigger
  a 15-minute lockout on the verification endpoint, server-side.
- Verification (`POST /settings/verify-pin`, and the equivalent check
  inline on the two delete endpoints) is a real server-side check, not a
  value compared in the frontend — a client can't just skip calling it.

## Known, accepted limitation: no API authentication on localhost

Every backend endpoint is reachable by any local process that can reach
`127.0.0.1:8765` — there is no API key, session token, or login gating
requests, only CORS restricted to the Vite dev origin (which stops a
browser tab from calling in, but not another local process).

This is a **deliberate, accepted gap for the current version**, not an
oversight:

- JARVIS is a single-user, single-machine app with no concept of "other
  users" to authenticate against.
- The realistic threat model is another process already running as you
  on your own machine — at that point it can generally already read your
  files, your browser's saved credentials, and your clipboard, so an
  unauthenticated localhost API is not the weakest link.
- Anything actually destructive on top of that (see above) still goes
  through the confirmation gate and, for deletes, the PIN — those don't
  rely on "no one else can reach the port" as their only defense.

This is deferred to a v2 authentication pass (a local token/session
scheme), tracked alongside the other deferred items in
`docs/PRE_PRODUCTION_AUDIT.md`. If you expose port 8765 beyond
`localhost` (e.g. binding `0.0.0.0` and opening it on your network or
the internet), that changes this threat model entirely — don't do that
without adding auth first.
