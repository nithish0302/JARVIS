# JARVIS

A desktop AI assistant for Windows: voice-activated, remembers things about
you across sessions, can act on your behalf (email, calendar, GitHub,
files, system commands), and runs against whichever LLM provider you give
it a key for.

Written for someone setting this up cold — a future version of the author
with no memory of this session, or anyone else picking up the repo.

## What it is

- **Voice assistant** — wake word ("wake up jarvis"), continuous
  follow-up conversation without repeating the wake word, TTS replies,
  interrupt phrases mid-response.
- **Chat UI** — a 2D/3D reactive "AI Core" orb + graph-style HUD, text
  chat alongside voice.
- **Long-term memory** — extracts and recalls facts about you across
  conversations (semantic search over a local vector store).
- **Plugins** — Gmail, Google Calendar, GitHub, and weather, invocable by
  voice or chat. (Spotify and WhatsApp are stubbed in the code but not
  wired up — see Known limitations.)
- **Personality modes** — Assistant / Developer / Research, plus
  modifiers (Planner, Quiet) layered on top.
- **Desktop automation** — open/close apps, file operations, system
  queries, PowerShell-backed actions — with destructive actions (deleting
  files, sending email, creating events/issues) gated behind an explicit
  confirmation step enforced server-side, not just in the UI. See
  [SECURITY.md](SECURITY.md).

## Prerequisites

- **Windows 11.** The installer, credential encryption (Windows DPAPI),
  and desktop automation are all Windows-specific; this does not run on
  macOS/Linux as shipped.
- **An NVIDIA GPU is recommended, not required.** Whisper transcription
  and the Kokoro TTS engine use CUDA when a compatible NVIDIA GPU and
  drivers are present, and fall back to CPU otherwise (slower, but
  functional). No AMD/Intel GPU acceleration path exists.
- **Internet connection on first launch.** The installer itself is small;
  the actual backend runtime is downloaded on first run (see below). You
  can use JARVIS offline after that *only* if you're also running a local
  Ollama model — every other provider (Gemini/Groq/OpenRouter) needs a
  connection to answer at all.
- At least one AI provider API key (Gemini, Groq, or OpenRouter — free
  tiers exist for all three) unless you're running Ollama locally.

## Installation

There are two ways to run this. Pick one.

### A) Install via installer (for actually using JARVIS day to day)

This is a **two-stage** process — the installer alone does not give you a
working app yet.

**Stage 1 — install the app shell:**

1. Get `JARVIS_<version>_x64-setup.exe` (~82MB). As of this writing there
   is no published, versioned installer release yet — build it yourself
   with `pnpm tauri build` from `apps/desktop` (see Run from source
   below for the prerequisite setup), which produces it at
   `apps/desktop/src-tauri/target/release/bundle/nsis/`. If a real
   Release later gets published, it belongs on the repo's normal
   [Releases](https://github.com/nithish0302/JARVIS/releases) page — not
   the `sidecar-runtime-v1` one, which is internal plumbing (see below)
   and has no installer in it, only the backend runtime asset.
2. Run it. This installs the frontend (the Tauri/React app) and a small
   backend launcher binary to `%LOCALAPPDATA%\JARVIS`. It does **not**
   install the actual AI backend runtime — that installer is
   deliberately kept small.

**Stage 2 — first launch downloads the backend runtime:**

3. Launch JARVIS. On this **first launch only**, it detects the backend
   runtime is missing and automatically downloads it (~2.1GB, split
   across two GitHub Release assets from the `sidecar-runtime-v1`
   release, reassembled and checksum-verified on your machine). You'll
   see a full-screen progress overlay:

   ```
   Setting up JARVIS
   [████████░░░░░░░░░░░░░░░░░░░░░░░░]
   Downloading JARVIS engine components... 45%
   ```

   This takes anywhere from under a minute to several minutes depending
   on your connection — it is not frozen, just downloading. Do not force-
   quit during this step.
4. **If the download fails or is interrupted** (network drop, app
   closed, insufficient disk space), the overlay switches to an error
   message and a **Retry** button. Retrying is always safe: any partial
   or corrupted data from the previous attempt is discarded first, so it
   always starts that attempt clean rather than resuming into a
   potentially-corrupt half-state. A disk-space check runs before the
   download starts and fails fast with a clear message if you don't have
   enough free space (needs roughly 10GB free headroom during setup;
   final on-disk footprint is ~3.7GB).
5. Once setup completes, the overlay disappears and the app behaves
   normally from then on. **Every subsequent launch skips straight to
   normal startup** — it finds the runtime already in place and never
   re-downloads it. (Full technical detail on how this works:
   `apps/desktop/src-tauri/src/sidecar_setup.rs` and
   `docs/SIDECAR_RUNTIME_RELEASE.md`.)

Then continue to [First-run setup](#first-run-setup-both-install-paths)
below.

**Total disk footprint:** ~82MB installer + ~3.7GB backend runtime
(after the one-time download) + Whisper model weights, which download
*separately* the first time you actually use voice (pulled from
HuggingFace's cache on demand — unrelated to the installer, a few hundred
MB depending on model size).

### B) Run from source (for modifying code)

Needs [uv](https://docs.astral.sh/uv/) (Python package/workspace manager)
and [pnpm](https://pnpm.io/) `^11.18.0` — this repo uses pnpm workspaces
for JS/TS and uv workspaces for Python; don't use `npm`/`yarn`/`pip`
directly.

```bash
# 1. Install JS dependencies (from repo root)
pnpm install

# 2. Install Python dependencies
cd services/jarvis-engine
uv sync

# 3. Copy the env template and fill in at least one provider key
cp .env.example .env
# edit .env - see First-run setup below for what goes where
```

Then, in two separate terminals:

```bash
# Terminal 1 - backend (from services/jarvis-engine)
uv run python start.py

# Terminal 2 - frontend + Tauri shell (from apps/desktop)
pnpm tauri dev
```

Running from source, `_internal` staging/download doesn't apply — the
Python backend just runs directly via `uv run`, so none of Stage 2 above
happens; you skip straight to a working backend. Only the installer path
needs the sidecar runtime download.

Building a release installer yourself (`pnpm tauri build` from
`apps/desktop`) requires first producing the PyInstaller
`_internal` build (see `services/jarvis-engine/jarvis-engine.spec`) and,
if you want the download-on-first-run behavior to work for anyone else,
re-cutting the GitHub Release per `docs/SIDECAR_RUNTIME_RELEASE.md`.

## First-run setup (both install paths)

JARVIS works with zero configuration for basic chat *if* you set at
least one provider key. Everything below is optional beyond that.

### AI provider

Open **Settings > Providers**. This is where the actual keys used by the
fallback cascade (Gemini → OpenRouter → Groq → Ollama, tried in that
order) live — saved encrypted, not as plaintext `.env` values, and
applied without restarting the app:

- **Gemini API key** — get one free at
  [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **Groq API key** — free at [console.groq.com](https://console.groq.com/keys).
- **OpenRouter API key** — free-tier models available at
  [openrouter.ai](https://openrouter.ai/keys).
- **Ollama Host** — *optional*, and not bundled with JARVIS. Only fill
  this in if you already have your own
  [Ollama](https://ollama.com/) instance running somewhere (locally or
  on your network) — e.g. `http://192.168.1.x:11434` or
  `http://localhost:11434`. Leave it empty to run on cloud providers
  only.

You only need one of these for JARVIS to answer at all; more than one
lets the fallback cascade recover automatically if one provider is down
or rate-limited. There's a separate **Settings > AI Provider** section
for overriding which single provider/model is preferred instead of the
default cascade order, and for picking a specific model name per
provider.

### Plugins

Open **Settings > Plugins**. Each row shows Connected / Not connected
with a Connect/Disconnect button.

**Gmail and Google Calendar** (one shared Google OAuth grant covers
both):

1. This requires you to have your own Google OAuth client — JARVIS does
   not ship with one. In [Google Cloud Console](https://console.cloud.google.com/):
   create a project (or use an existing one), enable the Gmail API and
   Google Calendar API, create an OAuth 2.0 Client ID (type: Desktop app
   or Web app), and add `http://localhost:8765/plugins/google/callback`
   as an authorized redirect URI.
2. Add the resulting client ID/secret to `services/jarvis-engine/.env`
   as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (these two are **not**
   in `.env.example` — add them yourself) and restart the backend.
3. Click **Connect** next to Gmail (or Google Calendar — either triggers
   the same grant). A browser tab opens for the Google consent screen.
   Approve it. The tab shows "Authentication successful! You can close
   this tab." — close it and both Gmail and Calendar show Connected.

**GitHub:**

1. Click **Connect** next to GitHub.
2. Click the link that appears
   (`github.com/settings/personal-access-tokens/new`) to create a
   **fine-grained personal access token**.
3. Scope it to this specific use (repository access: either "All
   repositories" or just the ones you want JARVIS to see) with these
   repository permissions:
   - **Contents: Read-only** (list repos, search code)
   - **Issues: Read and write** (list, search, *and create* issues —
     read-only will let creation fail)
   - **Pull requests: Read-only** (list PRs, check PR status)
   - **Metadata: Read-only** (required automatically)
4. Paste the generated token into the field next to GitHub and click
   **Save**.

**Weather:** no setup — it's backed by Open-Meteo, which needs no API
key. Connected by default.

**Spotify / WhatsApp:** shown in some capability lists but not actually
wired up yet — clicking Connect does nothing useful. See Known
limitations.

## Basic usage

- **Wake word:** say **"wake up jarvis"** to start a voice session.
  JARVIS acknowledges, then listens for your command.
- **Continuous conversation mode:** after the first command in a wake-word
  session, JARVIS keeps listening for follow-ups *without* needing the
  wake word again, for up to ~50 seconds of silence. Exit it by saying
  any of: *"stop listening jarvis"*, *"jarvis go to sleep"*, *"that's all
  jarvis"*, *"jarvis I will talk to you later"*, or the bare forms *"go to
  sleep"* / *"stop listening"* / *"that's all"*.
- **Interrupting JARVIS while it's talking:** say *"stop"*, *"wait"*,
  *"cancel"*, *"never mind"*, or *"hold on"* to cut off playback. Saying
  the wake phrase again mid-response starts a fresh wake cycle instead.
- **Chat mode:** type instead of talking — same backend, same plugins,
  same confirmation gates for destructive actions.
- **Personality modes** (Settings > Personality, or say "switch to
  developer mode" / "switch to research mode"):
  - **Assistant** — the default, general-purpose tone.
  - **Developer** — expert software engineer / systems architect framing.
  - **Research** — deep analytical/investigative framing.
- **Modifiers**, layered on top of whichever mode is active:
  - **Planner** — structured, step-by-step plans.
  - **Quiet** — minimal, concise output.
  - **None** — clears any active modifier.
- **What each plugin can do**, by voice or chat, once connected:
  - *Gmail:* check unread mail, search email, send email (send requires
    confirmation — see SECURITY.md).
  - *Google Calendar:* check today's/upcoming events, create an event
    (requires confirmation).
  - *GitHub:* list your repos, list/search issues, create an issue
    (requires confirmation), list PRs, check PR/commit status, search
    code.
  - *Weather:* current conditions and multi-day forecast for a named
    location.

## Known limitations

Read this before assuming something is broken — these are current,
known gaps, not accidents:

- **Ollama is not bundled and needs a separately-running instance.**
  JARVIS can talk to one if you point it at a host, but it doesn't
  install or manage Ollama for you.
- **Plugin setup is manual.** Gmail/Calendar need you to create your own
  Google OAuth client (Google doesn't allow a shipped-in-the-app secret
  for a desktop OAuth flow at this trust level); GitHub needs you to
  generate and paste in your own fine-grained PAT. Neither is a
  one-click "sign in" today.
- **GPU acceleration needs specific NVIDIA hardware + drivers** (CUDA).
  Everything still works without it — Whisper transcription and TTS just
  run on CPU instead, noticeably slower.
- **First launch requires internet** for the ~2.1GB backend runtime
  download described above; there is no offline installer variant yet.
- **Spotify and WhatsApp plugins are stubbed, not functional** — they
  appear in some internal capability lists but have no working backend
  integration or credential flow.
- **Single-user, local-machine design.** There's no login/auth system;
  see SECURITY.md for what that does and doesn't mean for you.
