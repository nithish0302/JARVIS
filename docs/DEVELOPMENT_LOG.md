# JARVIS Development Log

## Purpose

This append-only log records reconstructed engineering history from the
repository, project documentation, accepted ADRs, approved milestone plans,
and completed implementation work. Exact dates are not available for several
entries; those entries are ordered by documented ADR number or milestone
sequence rather than by a verified timestamp.

---

## Documented project baseline

**Date:** Could not be reconstructed.

**Objective:** Define a long-term, production-quality desktop AI assistant and
its initial engineering constraints before feature development.

**Decisions made:**

- JARVIS is a premium desktop AI operating companion, not a generic chatbot
  or an Iron Man UI replica.
- Development begins with a foundation phase before user-facing feature phases.
- The documented desktop application location is `apps/desktop`.
- The design language is 70% modern desktop application and 30% Iron Man
  inspiration, with usability taking priority over visual effects.

**Files created or modified:**

- `docs/architecture/PROJECT.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DESIGN_SYSTEM.md`
- `docs/architecture/ROADMAP.md`
- `docs/guides/AI_AGENT_GUIDE.md`
- `docs/guides/DEVELOPMENT_RULES.md`

The exact creation or modification history for these files cannot be
reconstructed from the available repository state.

**Outcome:** Phase 0 was defined as the project foundation: documentation,
folder structure, global theme, reusable components, and initial application
layout.

**Current status:** The baseline documents remain active and are the source of
truth for implementation decisions.

---

## Accepted architecture decisions

**Date:** Could not be reconstructed. ADR numbering provides the available
sequence.

**Objective:** Record foundational technology and product-architecture choices.

**Decisions made:**

1. **ADR 0001:** Use Tauri v2 rather than Electron for a smaller, secure
   desktop application with a Rust backend.
2. **ADR 0002:** Use Zustand for lightweight global state while retaining
   React state for component-local state.
3. **ADR 0003:** Use the Iron Hybrid design language: 70% modern desktop
   application and 30% Iron Man inspiration.
4. **ADR 0004:** Keep AI providers behind a provider-independent abstraction.

**Files created or modified:**

- `docs/adr/0001-use-tauri.md`
- `docs/adr/0002-use-zustand.md`
- `docs/adr/0003-design-philosophy.md`
- `docs/adr/0004-ai-provider-strategy.md`

The exact authoring dates and decision owners cannot be reconstructed.

**Outcome:** The accepted decisions define the desktop/runtime boundary,
state-management direction, visual philosophy, and future AI-provider
boundary.

**Current status:** All four ADRs are accepted and active.

---

## Phase 0 — Milestone 1: Tauri template cleanup

**Date:** Could not be reconstructed from repository timestamps. Completed
before Milestone 2.

**Objective:** Remove default Tauri/Vite demonstration behavior and establish
the JARVIS desktop identity without implementing application features.

**Decisions made:**

- Use `apps/desktop` as the canonical desktop application, matching the
  documented architecture.
- Remove the template greeting command and the unused opener plugin/capability.
- Set the application product name and title to `JARVIS`.
- Set the bundle identifier to `com.nithish.jarvis`.
- Retain `public/vite.svg` because `index.html` still references it as the
  favicon; no JARVIS icon asset was available.

**Files created or modified:**

- Modified `apps/desktop/src/App.tsx`
- Modified `apps/desktop/src/test/App.test.tsx`
- Modified `apps/desktop/package.json`
- Regenerated `pnpm-lock.yaml`
- Modified `apps/desktop/src-tauri/Cargo.toml`
- Regenerated `apps/desktop/src-tauri/Cargo.lock`
- Modified `apps/desktop/src-tauri/src/lib.rs`
- Modified `apps/desktop/src-tauri/src/main.rs`
- Modified `apps/desktop/src-tauri/tauri.conf.json`
- Modified `apps/desktop/src-tauri/capabilities/default.json`
- Deleted `apps/desktop/src/assets/react.svg`
- Deleted `apps/desktop/public/tauri.svg`

**Outcome:** The canonical desktop app no longer exposes the template greeting
command or opener capability. It presents a minimal JARVIS root and compiles
without those template dependencies.

**Current status:** Complete and accepted.

---

## Phase 0 — Milestone 2: Design foundation

**Date:** Could not be reconstructed from repository timestamps. Completed
after Milestone 1.

**Objective:** Establish CSS-only design foundations without creating UI
components, layouts, pages, or product features.

**Decisions made:**

- Use semantic CSS custom properties as the source of truth for design values.
- Define tokens in both `:root` and `[data-theme="dark"]` for future theme
  readiness, with identical current dark values.
- Use Inter with a system UI fallback without adding a font dependency.
- Keep global styles in `src/styles` rather than attaching them to `App`.

**Files created or modified:**

- Created `apps/desktop/src/styles/tokens.css`
- Created `apps/desktop/src/styles/globals.css`
- Modified `apps/desktop/src/main.tsx`
- Modified `apps/desktop/src/App.tsx`
- Deleted `apps/desktop/src/App.css`

**Outcome:** The application now has semantic colors, typography, spacing,
radius, border, shadow, glow, motion, and global accessibility/reduced-motion
foundations.

**Current status:** Complete and accepted.

---

## Phase 0 — Milestone 3: Reusable UI primitives

**Date:** Could not be reconstructed from repository timestamps. Completed
after Milestone 2.

**Objective:** Create reusable, accessible UI primitives without implementing
pages, layouts, AI features, chat, or business logic.

**Decisions made:**

- Create Button, IconButton, Input, Card, and StatusIndicator primitives in
  the documented `components/ui` folder.
- Use `React.forwardRef` for Button, IconButton, and Input.
- Add `clsx` through a shared `cn` utility for class composition.
- Centralize Button and IconButton style recipes to avoid duplicated Tailwind
  class combinations.
- Do not add test files in this milestone, per the approved scope.

**Files created or modified:**

- Created `apps/desktop/src/lib/cn.ts`
- Created `apps/desktop/src/components/ui/Button.tsx`
- Created `apps/desktop/src/components/ui/IconButton.tsx`
- Created `apps/desktop/src/components/ui/Input.tsx`
- Created `apps/desktop/src/components/ui/Card.tsx`
- Created `apps/desktop/src/components/ui/StatusIndicator.tsx`
- Created `apps/desktop/src/components/ui/buttonStyles.ts`
- Modified `apps/desktop/package.json`
- Regenerated `pnpm-lock.yaml`

**Outcome:** The desktop app has typed, token-driven, accessible primitive
components ready for later composition. They are not yet rendered by the
application shell.

**Current status:** Complete and accepted.

---

## Phase 0 — Milestone 3 refinement: Interaction states

**Date:** Could not be reconstructed from repository timestamps. Completed
after Milestone 3.

**Objective:** Correct documented interaction details identified during the
Milestone 3 self-review.

**Decisions made:**

- Add semantic disabled-opacity and active-scale tokens rather than use literal
  opacity or scale values in components.
- Apply a token-based cyan `focus-within` border to Input.
- Apply token-based hover emphasis, active scale reduction, and disabled
  opacity to the shared Button and IconButton styling.

**Files created or modified:**

- Modified `apps/desktop/src/styles/tokens.css`
- Modified `apps/desktop/src/components/ui/buttonStyles.ts`
- Modified `apps/desktop/src/components/ui/Input.tsx`

**Outcome:** Input, Button, and IconButton now align more closely with the
documented focused, hover, active, and disabled interaction rules.

**Current status:** Complete and accepted.

---

## Phase 0 — Milestone 4: Application shell

**Date:** Planning completed; implementation date not yet applicable.

**Objective:** Design the permanent desktop shell that will provide persistent
header, main-content, dock, scrolling, layering, accessibility, and window
sizing structure for future features.

**Decisions made:**

- A detailed implementation plan has been prepared, but no application-shell
  implementation approval has been recorded.
- The planned shell is intended to support future AI Core, chat, voice, and
  settings content without implementing those features now.

**Files created or modified:**

No application-shell files have been created or modified yet.

**Outcome:** Implementation is pending explicit approval.

**Current status:** Planned; awaiting implementation approval.

---

## Log maintenance

Append a new dated or explicitly date-unavailable entry after every approved
milestone. Do not rewrite prior entries except to correct a demonstrable factual
error; this document is append-only.

---

## Phase 0 — Milestone 4: Application shell implementation

**Date:** 2026-08-01

**Objective:** Implement the approved permanent desktop structure without
adding feature UI, application state, native commands, or business logic.

**Decisions made:**

- Use the approved structural composition: `App` → `LayoutProvider` →
  `AppShell` → `AppHeader`, `AppMain`, `OverlayLayer`, and main-content
  children.
- Keep `LayoutProvider` static and structural; it establishes the current dark
  theme boundary without creating a store or runtime theme-switching behavior.
- Keep `AppHeader` empty and structural. Brand, navigation, status, and actions
  remain deferred.
- Keep `OverlayLayer` empty and non-interactive. It reserves the semantic
  overlay layer without implementing overlay functionality.
- Do not create `AppDock`, modify `tauri.conf.json`, or introduce AI, chat,
  voice, settings, reusable UI components, Zustand stores, Tauri commands, or
  business logic.
- Make `AppMain` the only default vertical scroll container; prevent body and
  shell scrolling.

**Files created or modified:**

- Created `apps/desktop/src/components/layout/LayoutProvider.tsx`
- Created `apps/desktop/src/components/layout/AppShell.tsx`
- Created `apps/desktop/src/components/layout/AppHeader.tsx`
- Created `apps/desktop/src/components/layout/AppMain.tsx`
- Created `apps/desktop/src/components/layout/OverlayLayer.tsx`
- Modified `apps/desktop/src/App.tsx`
- Modified `apps/desktop/src/styles/tokens.css`
- Modified `apps/desktop/src/styles/globals.css`
- Modified `apps/desktop/src/test/App.test.tsx`

**Outcome:** The application now has a full-viewport, landmark-based shell with
a persistent structural header, a single default main scroll region, semantic
stacking tokens, a skip link, and an empty overlay layer. All layout components
remain below the approximate 150-line limit.

**Validation:** Desktop tests, lint, and production build passed. Static checks
confirmed body and shell overflow are hidden, `AppMain` owns default vertical
scrolling, and layout components contain no literal colors or z-index values.

**Current status:** Implementation complete; awaiting review before the next
milestone.
