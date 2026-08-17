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

## Phase 0 â€” Milestone 1: Tauri template cleanup

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

## Phase 0 â€” Milestone 2: Design foundation

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

## Phase 0 â€” Milestone 3: Reusable UI primitives

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

## Phase 0 â€” Milestone 3 refinement: Interaction states

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

## Phase 0 â€” Milestone 4: Application shell

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

## Phase 0 â€” Milestone 4: Application shell implementation

**Date:** 2026-08-01

**Objective:** Implement the approved permanent desktop structure without
adding feature UI, application state, native commands, or business logic.

**Decisions made:**

- Use the approved structural composition: `App` â†’ `LayoutProvider` â†’
  `AppShell` â†’ `AppHeader`, `AppMain`, `OverlayLayer`, and main-content
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

---

## Phase 0 - Milestone 6A: Base UI Component Library - Core Primitives

**Date:** 2026-08-01

**Objective:** Establish the first half of the permanent JARVIS base UI
component library without adding feature-specific UI, business logic, or
animation framework usage.

**Decisions made:**

- Split the previously approved UI-library scope into two implementation
  milestones. Milestone 6A contains Button, IconButton, Card, Panel, Badge,
  Divider, Field, and Input; the remaining components are deferred to
  Milestone 6B.
- Give every reusable component its own folder and `README.md` so its purpose,
  public API, accessibility expectations, and usage are maintained beside its
  implementation.
- Preserve the accepted Button, IconButton, Card, and Input public APIs while
  relocating them into the permanent component structure.
- Add `Panel` as a distinct semantic section surface while retaining Card's
  existing `panel` variant for backward compatibility.
- Centralize common action and surface style recipes to avoid duplicated
  Tailwind class combinations.
- Introduce `Field` and `useFieldIds` as the shared accessible field
  composition foundation; refactor Input internally to consume it without
  changing Input's public API.
- Use only existing semantic design tokens. No Framer Motion, feature-specific
  UI, stores, Tauri commands, or product business logic were introduced.

**Files created or modified:**

- Relocated and modified `apps/desktop/src/components/ui/Button/Button.tsx`
- Relocated and modified `apps/desktop/src/components/ui/IconButton/IconButton.tsx`
- Relocated and modified `apps/desktop/src/components/ui/Card/Card.tsx`
- Relocated and modified `apps/desktop/src/components/ui/Input/Input.tsx`
- Created `apps/desktop/src/components/ui/Panel/Panel.tsx`
- Created `apps/desktop/src/components/ui/Badge/Badge.tsx`
- Created `apps/desktop/src/components/ui/Divider/Divider.tsx`
- Created `apps/desktop/src/components/ui/Field/Field.tsx`
- Created `apps/desktop/src/components/ui/Field/useFieldIds.ts`
- Created `apps/desktop/src/components/ui/shared/buttonStyles.ts`
- Created `apps/desktop/src/components/ui/shared/surfaceStyles.ts`
- Created component README and test files for every Milestone 6A component.
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The project now has a documented, token-driven, accessible core
component foundation. Native interactive controls preserve keyboard behavior,
Input composes the shared field contract, and all components remain independent
of application features.

**Validation:** Pending execution after implementation.

**Current status:** Implementation complete; awaiting review before Milestone
6B.

---

## Phase 0 - Milestone 6A: Validation

**Date:** 2026-08-01

**Objective:** Verify the completed Milestone 6A component-library foundation.

**Decisions made:**

- Validate the library with focused component tests, linting, a TypeScript
  production build, and static source checks.
- Retain the initial implementation after validation; no corrective production
  code changes were required.

**Files created or modified:**

- Modified `apps/desktop/src/components/ui/Button/Button.test.tsx`
- Modified `apps/desktop/src/components/ui/Field/Field.test.tsx`
- Modified `docs/CURRENT_STATUS.md`
- Appended this validation entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** All nine test files and all nine tests passed. ESLint and the
production TypeScript/Vite build passed. No literal hexadecimal colors exist in
the UI component source, common action and surface class recipes are shared,
and every component source file remains below 150 lines.

**Current status:** Milestone 6A is verified and awaiting review before
Milestone 6B.

---

## Phase 0 - Milestone 6B: Base UI Component Library - Extended Primitives

**Date:** 2026-08-01

**Objective:** Complete the approved remaining foundational UI component
library without implementing application features.

**Decisions made:**

- Implement only Textarea, Select, Checkbox, Switch, Spinner, Skeleton, and
  StatusIndicator; EmptyState, ProgressBar, layouts, overlays, and product
  features remain out of scope.
- Reuse the existing Field and useFieldIds composition for all new form
  controls, and centralize shared direct-control styles for Input, Textarea,
  and Select.
- Retain native controls and forward refs for Textarea, Select, Checkbox, and
  Switch so keyboard, focus, and form integration remain native.
- Add a minimal token-driven Spinner rotation. It is enabled only when the
  user does not request reduced motion and uses the existing slow-duration and
  standard-easing tokens.
- Keep Skeleton static and hidden from assistive technology. It does not add a
  continuous loading animation.
- Relocate StatusIndicator into its own component folder, preserve its public
  API, and use the semantic full-radius token for its marker.
- Add a README and focused test for every Milestone 6B component, including
  expected future consumers in each README's Used By section.

**Files created or modified:**

- Created `apps/desktop/src/components/ui/shared/fieldControlStyles.ts`
- Modified `apps/desktop/src/components/ui/Input/Input.tsx`
- Created Textarea, Select, Checkbox, Switch, Spinner, Skeleton, and
  StatusIndicator component folders, each containing implementation, test, and
  README files.
- Deleted the former `apps/desktop/src/components/ui/StatusIndicator.tsx`
  after relocating it to its self-contained component folder.
- Modified `apps/desktop/src/styles/globals.css`
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The base UI component library now provides the approved
foundational form, loading, and status primitives. Components remain reusable,
independent of product behavior, token-driven, and accessible through native
semantics and shared field composition.

**Validation:** All 16 test files and all 16 tests passed. ESLint and the
production TypeScript/Vite build passed. Static checks confirmed that every
Milestone 6B component has its README and test file, that component source has
no literal hexadecimal colors, spacing, radii, shadows, typography, or timing
values, and that all component files remain below 150 lines.

**Current status:** Implementation complete; awaiting review before any next
milestone.

---

## Phase 0 - Milestone 6B: Documentation consistency

**Date:** 2026-08-01

**Objective:** Keep the canonical visual documentation aligned with the
approved Spinner implementation.

**Decisions made:**

- Record the narrow Spinner exception to the AI Core-only continuous-animation
  rule. The Spinner rotation is limited to loading feedback, uses semantic
  motion tokens, and respects reduced-motion preferences.

**Files created or modified:**

- Modified `docs/architecture/DESIGN_SYSTEM.md`
- Modified `docs/architecture/DESIGN_TOKENS.md`
- Modified `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The canonical documentation now matches the approved Spinner
behavior.

**Current status:** Milestone 6B remains complete and awaiting review.

---

## Phase 0 â€” Milestone 5: Design System Foundation

**Date:** 2026-08-01

**Objective:** Formalize the design-token system and document a canonical
specification without implementing application features or theme switching.

**Decisions made:**

- Create `DESIGN_TOKENS.md` as the canonical token specification and require
  `tokens.css` to follow it.
- Keep dark theme as the only supported theme. Do not introduce `theme.ts`, a
  typed theme model, a switcher, or a Zustand store until multiple themes
  exist.
- Preserve current component usage and only update primitives where a newly
  introduced semantic token directly replaces an existing generic token.
- Add semantic typography, focus, elevation, blur, icon-size, full-radius,
  opacity, and future motion-transition tokens.
- Keep current shadow usage unchanged while reserving a large shadow tier for
  future high-elevation surfaces.

**Files created or modified:**

- Created `docs/architecture/DESIGN_TOKENS.md`
- Modified `apps/desktop/src/styles/tokens.css`
- Modified `apps/desktop/src/styles/globals.css`
- Modified `apps/desktop/src/components/ui/buttonStyles.ts`
- Modified `apps/desktop/src/components/ui/Input.tsx`
- Modified `apps/desktop/src/test/App.test.tsx`

**Outcome:** JARVIS now has a documented, semantic design-token contract for
dark-theme colors, typography, spacing, radii, borders, shadows, blur, glow,
icons, motion, opacity, focus, and layering. No feature UI, dynamic theme
model, state, or new component was introduced.

**Validation:** Tests, lint, and production build passed. Every documented
token is defined in `tokens.css`, and every token reference in `src` resolves.

**Current status:** Implementation complete; awaiting review before the next
milestone.

---

## Phase 1 - Milestone 1: Header and Status Bar

**Date:** 2026-08-01

**Objective:** Implement the persistent top navigation (Header) and bottom global status reporting (Status Bar) areas within the desktop application shell.

**Decisions made:**

- Maintain the `AppShell` grid layout structure, updating it to include a third row for the `StatusBar`.
- Expose a reusable brand area in `AppHeader` rather than hardcoding branding. Use styled typography ("JARVIS") as a temporary placeholder.
- Create `StatusBar` as a presentation-only layout component with placeholder slots for future status injection. It does not hardcode application state (e.g., "System Ready") or integrate loading indicators like `Spinner`, which belong to future feature modules.

**Files created or modified:**

- Modified `apps/desktop/src/components/layout/AppHeader.tsx`
- Created `apps/desktop/src/components/layout/StatusBar.tsx`
- Modified `apps/desktop/src/components/layout/AppShell.tsx`
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The application shell now establishes the full vertical bounds defined in the design system, with a persistent header and status bar. The layout is prepared to accept the AI Core and Chat Interface in the main content area.

**Validation:** Desktop tests, lint, and production build passed.

**Current status:** Implementation complete; awaiting review before the next milestone.

---

## Phase 1 - Milestone 2: AI Core (Idle Experience)

**Date:** 2026-08-01

**Objective:** Establish the permanent central presentation of JARVIS before any conversation begins, including the glowing AI Core orb, identity typography, welcome greeting, and placeholder suggestion cards.

**Decisions made:**

- Render the IdleView directly through `AppMain` to preserve the application shell boundaries without modifying `App.tsx`.
- Create a modular `components/ai-core/` directory containing individual components for `AiCore`, `AiCoreIdle`, `AiIdentity`, `IdleView`, `SuggestionCard`, `SuggestionGrid`, and `WelcomeMessage`.
- Size the AI Core orb and its glow strictly using semantic design tokens (`var(--space-16)`, `var(--glow-md)`, `var(--color-highlight)`).
- Implement a subtle continuous animation using `framer-motion` in `AiCoreIdle`, with a fallback for `useReducedMotion`.
- Limit components to a strict 150-line boundary, providing individual tests and README documentation.

**Files created or modified:**

- Created `apps/desktop/src/components/ai-core/*` (AiCore, AiCoreIdle, AiIdentity, IdleView, SuggestionCard, SuggestionGrid, WelcomeMessage)
- Modified `apps/desktop/src/components/layout/AppMain.tsx`
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The application shell now displays the central visual identity of JARVIS when idle, maintaining semantic styling and responsive alignment without introducing business logic or active state management.

**Validation:** Desktop tests, lint, and production build passed.

**Current status:** Implementation complete; awaiting review before the next milestone.

---

## Phase 1 - Milestone 3: Chat Conversation Area

**Date:** 2026-08-01

**Objective:** Implement the permanent scrollable conversation region that displays AI and user messages, swapping with the IdleView appropriately, without business logic.

**Decisions made:**

- Kept `AppMain` purely generic, stripping its awareness of chat messages or `IdleView`.
- Created a `ChatView` component at the page composition layer to dictate the display of either `IdleView` or `ConversationArea` based on mock static messages.
- Centralized `Message` types in `apps/desktop/src/types/chat.types.ts`.
- Used semantic flex layouts and design tokens (`--color-surface`, `--color-accent`) for message bubbles, avoiding arbitrary dimensions.
- Managed automatic scrolling behavior entirely within `ConversationArea` using `scrollIntoView()` on a dummy anchor element.
- Added a `TypingIndicator` utilizing `framer-motion` that supports reduced-motion via a subtle opacity fade.

**Files created or modified:**

- Created `apps/desktop/src/types/chat.types.ts`
- Created `apps/desktop/src/components/chat/*` (ConversationArea, MessageList, MessageBubble, MessageAvatar, TypingIndicator, ChatView)
- Modified `apps/desktop/src/components/layout/AppMain.tsx` (Reverted to generic layout)
- Modified `apps/desktop/src/App.tsx` (Rendered `ChatView`)
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The application successfully renders the layout of a conversation, defaulting to mock placeholder data injected at the page level. Visual styling strictly follows the token design system without introducing hardcoded states.

**Validation:** Desktop tests, lint, and production build passed.

**Current status:** Refinements complete; awaiting final review.

---

### Architectural Refinements (Phase 1 - Milestone 3)

**Date:** 2026-08-01

**Refinements:**

- Restored `App.tsx` as the permanent application composition root without feature-specific logic.
- Composed the chat experience through the layout layer via `AppShell.tsx`, which now acts as the permanent page-level controller.
- Maintained `AppMain` as a purely generic layout container.

**Validation:** Tests, linting, and build passed successfully following refinements.

---

### Architectural Refinements (Phase 1 - Milestone 3 - Final)

**Date:** 2026-08-02

**Refinements:**

- Removed `ChatView` from `AppShell`. `AppShell` returned to being a pure layout component accepting `children` and passing them to `AppMain`.
- Updated `App.tsx` to render `<ChatView />` by passing it as a child of `<AppShell>`.
- Verified the compositional flow: `App.tsx` (Decides Feature) -> `AppShell` (Handles Layout) -> `AppMain` (Renders Children) -> `ChatView` (Owns Chat).

**Validation:** Desktop tests, lint, and production build passed.

## Phase 1 - Milestone 4: Chat Composer (Input Area)

**Date:** 2026-08-02

**Objective:** Implement the permanent chat input area where
the user types and sends messages, with keyboard accessibility
and auto-growing textarea behavior.

**Decisions made:**

- Use a plain <textarea> element directly inside ChatComposer
  rather than the existing Textarea UI component. Chat composers
  have no visible label â€” this is a documented legitimate
  exception. aria-label="Message" provides screen reader access.
- Auto-grow the textarea dynamically up to 5 lines using
  scrollHeight, then scroll internally.
- Handle Enter to send and Shift+Enter for newline at the
  keyboard event level inside ChatComposer.
- Show a character count warning styled with --color-text-muted
  and --font-size-caption tokens when the message exceeds 500
  characters, formatted as "523 / 500".
- Create ComposerToolbar as an empty placeholder for future
  actions (voice input, file attach, etc).
- Wire ChatComposer into ChatView using React useState so
  sending a message appends it to the local messages array,
  giving the illusion of a working chat for layout validation.
- Install lucide-react (previously accepted in design system
  ADR but not in package.json) and
  @testing-library/user-event (needed for keyboard simulation
  in tests).

**Files created or modified:**

- Created apps/desktop/src/components/chat/ChatComposer/ChatComposer.tsx
- Created apps/desktop/src/components/chat/ChatComposer/ChatComposer.test.tsx
- Created apps/desktop/src/components/chat/ChatComposer/README.md
- Created apps/desktop/src/components/chat/SendButton/SendButton.tsx
- Created apps/desktop/src/components/chat/SendButton/SendButton.test.tsx
- Created apps/desktop/src/components/chat/SendButton/README.md
- Created apps/desktop/src/components/chat/ComposerToolbar/ComposerToolbar.tsx
- Created apps/desktop/src/components/chat/ComposerToolbar/ComposerToolbar.test.tsx
- Created apps/desktop/src/components/chat/ComposerToolbar/README.md
- Modified apps/desktop/src/components/chat/ChatView/ChatView.tsx
- Modified apps/desktop/src/components/chat/ChatView/ChatView.test.tsx
- Modified apps/desktop/package.json
- Regenerated pnpm-lock.yaml
- Updated docs/CURRENT_STATUS.md

**Outcome:** The application now has a fully functional-looking
chat interface. The user can type a message, press Enter or
click Send, and see their message appear in the conversation
area. The IdleView disappears on the first message.
Auto-scroll works. The composer stays fixed at the bottom
while ConversationArea scrolls above it.

**Validation:** 35 tests passing, lint clean, production
build successful.

**Current status:** Complete and approved.

---

## Phase 1 - Milestone 5: Settings UI

**Date:** 2026-08-02

**Objective:** Implement the presentational Settings UI for JARVIS.

**Decisions made:**

- Utilize `App.tsx` local state to toggle between `"chat"` and `"settings"` views.
- Extend `AppShell` and `AppHeader` to support `onSettingsOpen` and `onClose` callbacks, rendering a Settings icon in Chat mode and a Back arrow in Settings mode.
- Introduce `SettingsView` as a new page-level orchestrator for settings.
- Introduce a two-column `SettingsLayout` and a vertical `SettingsSidebar`.
- Implement `AIProviderSection`, `AppearanceSection`, and `AboutSection` using existing UI primitives like `Select`, `Input`, and `Switch`.
- Enforce design system tokens for spacing, typography, and layout. No hardcoded styles were used.
- All new components include tests and `README.md` files, keeping each file under 150 lines.

**Files created or modified:**

- Modified `apps/desktop/src/App.tsx`
- Modified `apps/desktop/src/components/layout/AppShell.tsx`
- Modified `apps/desktop/src/components/layout/AppHeader.tsx`
- Created `apps/desktop/src/components/settings/*` (SettingsView, SettingsLayout, SettingsSidebar, SettingsSection, AIProviderSection, AppearanceSection, AboutSection)
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

**Outcome:** The user can now seamlessly toggle between the Chat View and the newly built Settings View using the AppHeader icons. Settings view features a functional left sidebar that switches out the main content sections. Everything is presentational but well-structured for future integrations.

**Validation:** Tests passing, lint clean, production build successful.

**Current status:** Complete and approved.

---

## Architecture Clarification: jarvis-engine Python Service

Date: 2026-08-02
Context: Repository contains scaffolded Python service at services/jarvis-engine/ with stubbed core modules.
Decision: jarvis-engine is the intended AI brain of JARVIS. It will house Provider Manager, Conversation Manager, Prompt Pipeline, Memory Interface, and Tool Calling. Currently empty scaffold only. No implementation until Phase 2 (AI Integration). Leave untouched during Phase 1.
Status: Noted and deferred to Phase 2.

## Architecture Clarification: packages/ui vs desktop ui

Date: 2026-08-02
Decision: apps/desktop/src/components/ui/ is the current local UI library. packages/ui/ is reserved for future shared cross-app library (Desktop + Android + Web). Do not migrate components during Phase 1. Migration happens when Android development begins. Never duplicate components in both locations.
Status: Migration deferred to Phase 8 or later.

## Architecture Clarification: packages/shared-types

Date: 2026-08-02
Decision: apps/desktop/src/types/ holds app-local types. packages/shared-types/ is reserved for cross-application TypeScript contracts. Keep chat.types.ts in desktop app. Rule: Only migrate a type when consumed by 2+ apps. Types shared with Python need language-neutral contracts such as OpenAPI or JSON Schema.
Status: Migration deferred until second consumer exists.

## Phase 1 - Milestone 6: Desktop Polish

Date: 2026-08-02

Objective: Final visual and interaction polish before
AI integration begins.

Changes:

- App.tsx: AnimatePresence view transitions added
- ChatView.tsx: IdleView/ConversationArea crossfade,
  fixed Easing type import
- SuggestionCard.tsx: hover state added
- ChatComposer.tsx: top border separator added
- MessageBubble.tsx: max-w-70% cap added
- AppHeader.tsx: accent brand text + padding refined
- AppShell.tsx: StatusBar slots wired
- buttonStyles.ts + fieldControlStyles.ts: focus audit
- globals.css: webkit scrollbar styling added
- ci.yml: Node 22, uv path fix, user-event dependency
- package.json: @testing-library/user-event added

Validation: 51/51 tests, lint clean, build clean.
Status: Complete and approved.


## Phase 1 - Milestone 5: Settings UI

**Date:** 2026-08-02

**Objective:** Implement the presentational Settings UI for JARVIS.

**Decisions made:**

- Utilize `App.tsx` local state to toggle between `"chat"` and `"settings"` views.
- Extend `AppShell` and `AppHeader` to support `onSettingsOpen` and `onClose` callbacks, rendering a Settings icon in Chat mode and a Back arrow in Settings mode.
- Introduce `SettingsView` as a new page-level orchestrator for settings.
- Introduce a two-column `SettingsLayout` and a vertical `SettingsSidebar`.
- Implement `AIProviderSection`, `AppearanceSection`, and `AboutSection` using existing UI primitives like `Select`, `Input`, and `Switch`.
- Enforce design system tokens for spacing, typography, and layout. No hardcoded styles were used.
- All new components include tests and `README.md` files, keeping each file under 150 lines.

**Files created or modified:**

- Modified `apps/desktop/src/App.tsx`
- Modified `apps/desktop/src/components/layout/AppShell.tsx`
- Modified `apps/desktop/src/components/layout/AppHeader.tsx`
- Created `apps/desktop/src/components/settings/*` (SettingsView, SettingsLayout, SettingsSidebar, SettingsSection, AIProviderSection, AppearanceSection, AboutSection)
- Updated `docs/CURRENT_STATUS.md`
- Appended this entry to `docs/DEVELOPMENT_LOG.md`

## Phase 4 - Milestone 1: Desktop Automation Refinements & Bug Fixes

**Date:** 2026-08-17

**Objective:** Refine automation parsing, handle multiple actions safely, fix URL handling, and improve application search accuracy.

**Decisions made:**
- Changed LLM response format for automation from single JSON objects to JSON arrays to support multiple simultaneous actions (e.g. opening two apps).
- Integrated `react-markdown` to safely render markdown output in `ChatFullView` and `StreamingMessage`.
- Allowed `open_url` UI Actions to be parsed safely and routed to the correct system browsers via a Rust `open_url_in_browser` command.
- Expanded Rust `find_application` search parameters to include `%APPDATA%` and `%LOCALAPPDATA%\Programs`.
- Cleaned PowerShell output from cluttering chat history.

**Outcome:** JARVIS reliably processes multi-step automation commands.

**Validation:** 63/63 desktop tests pass. `cargo build`, `pnpm build`, and `pnpm lint` succeed.

## Phase 4 - Milestone 1: Fixes before Milestone 2

**Date:** 2026-08-17

**Objective:** Prevent automation false positives for web search queries and support searchable URLs (like Microsoft Store).

**Decisions made:**
- Updated `needs_automation()` in `routes.py` with smarter exclusions to ignore questions containing words like "is", "available", "exist" even if they contain automation trigger words like "store".
- Added `ms-windows-store://` protocol handling in `open_url_in_browser` in `lib.rs` to allow searching inside the Microsoft Store.
- Updated `COMMAND_GENERATION_PROMPT` with searchable URL patterns (YouTube, Google, Amazon India, Microsoft Store, GitHub, Stack Overflow) to allow opening an app/website and immediately searching a query.

**Outcome:** JARVIS can now differentiate between asking about an app (which triggers web search) and commanding to open it and search within it (which triggers an `OPEN_URL` UI Action).

**Validation:** Python API routes tested successfully. `cargo build` in `src-tauri` will compile the new Windows Store handler.

**Outcome:** The user can now seamlessly toggle between the Chat View and the newly built Settings View using the AppHeader icons. Settings view features a functional left sidebar that switches out the main content sections. Everything is presentational but well-structured for future integrations.

**Validation:** Tests passing, lint clean, production build successful.

**Current status:** Complete and approved.

---

## Architecture Clarification: jarvis-engine Python Service
Date: 2026-08-02
Context: Repository contains scaffolded Python service at services/jarvis-engine/ with stubbed core modules.
Decision: jarvis-engine is the intended AI brain of JARVIS. It will house Provider Manager, Conversation Manager, Prompt Pipeline, Memory Interface, and Tool Calling. Currently empty scaffold only. No implementation until Phase 2 (AI Integration). Leave untouched during Phase 1.
Status: Noted and deferred to Phase 2.

## Architecture Clarification: packages/ui vs desktop ui
Date: 2026-08-02
Decision: apps/desktop/src/components/ui/ is the current local UI library. packages/ui/ is reserved for future shared cross-app library (Desktop + Android + Web). Do not migrate components during Phase 1. Migration happens when Android development begins. Never duplicate components in both locations.
Status: Migration deferred to Phase 8 or later.

## Architecture Clarification: packages/shared-types
Date: 2026-08-02
Decision: apps/desktop/src/types/ holds app-local types. packages/shared-types/ is reserved for cross-application TypeScript contracts. Keep chat.types.ts in desktop app. Rule: Only migrate a type when consumed by 2+ apps. Types shared with Python need language-neutral contracts such as OpenAPI or JSON Schema.
Status: Migration deferred until second consumer exists.

## Phase 2 - Milestone 1: Zustand Stores + Remove Mock Data

**Date:** 2026-08-07

**Objective:** Implement global state management using Zustand and remove static UI mock data from the chat experience.

**Decisions made:**
- Integrated `zustand` for domain-specific global state.
- Created `useConversationStore` to manage active chat thread, messages, and typing indicator.
- Created `useAIStore` to manage model configurations and generation state.
- Created `usePersonalityStore` to manage behavioral dials.
- Created `useAppStore` to control high-level navigation (chat vs settings).
- Refactored `App.tsx` and `ChatView.tsx` to read and write to global state instead of using isolated local `useState` for core application data.
- Mock data (`INITIAL_MOCK_MESSAGES`) previously used to validate presentation logic has been completely removed.
- Tests were updated to reflect the newly integrated state logic (`IdleView` is now the default rendered state until a message is sent).

**Next steps:**
- Proceed to Phase 2 - Milestone 2 (Backend AI connections).

## Phase 2 - Milestone 2: jarvis-engine FastAPI Server

Date: 2026-08-08

Objective: Build the jarvis-engine FastAPI server 
foundation with provider abstraction layer and 
SQLite conversation storage.

Files created:
- services/jarvis-engine/src/jarvis_engine/core/
  config.py, database.py, models.py
- services/jarvis-engine/src/jarvis_engine/providers/
  base.py, manager.py, ollama.py, openrouter.py
- services/jarvis-engine/src/jarvis_engine/memory/
  conversation.py
- services/jarvis-engine/src/jarvis_engine/api/
  routes.py
- services/jarvis-engine/src/jarvis_engine/main.py
- services/jarvis-engine/start.py
- services/jarvis-engine/start.bat
- services/jarvis-engine/.env.example
- services/jarvis-engine/test_api.py

Validation:
- Server starts on http://localhost:8765
- GET /health returns status online, version 0.1.0,
  both providers listed (available: false â€” correct 
  for stubs)
- GET /providers returns both provider stubs
- POST /chat returns mock response
- SQLite database auto-created at data/jarvis.db
- CORS configured for Tauri port 1420

Status: Complete and approved.

## Phase 2 - Milestone 3: Ollama Real AI Connection

Date: 2026-08-08

Objective: Replace mock AI responses with real 
Ollama llama3.2:3b responses.

Files modified:
- providers/ollama.py â€” real httpx Ollama connection
- providers/manager.py â€” real provider routing
- api/routes.py â€” JARVIS system prompt + history
- main.py â€” startup provider availability logging
- test_api.py â€” 4 integration tests

Validation results:
- Health: PASS â€” Ollama available true
- Chat 1: PASS â€” Real AI response received
- Chat 2: PASS â€” Conversation context maintained
- History: PASS â€” 4 messages in SQLite

JARVIS personality active â€” responds as sir,
maintains context, never uses filler phrases.

Status: Complete and approved.

## Phase 2 - Milestone 4: Connect Desktop UI to jarvis-engine

**Date:** 2026-08-09

**Objective:** Connect the React frontend to the real jarvis-engine FastAPI server.

**Decisions made:**

- Created API client service \jarvisApi.ts\ using native \etch\.
- Created \useJarvisChat.ts\ hook to handle chat logic, removing local state from \ChatView\.
- Created \useEngineStatus.ts\ hook to poll jarvis-engine health and update \useAIStore\.
- Updated \useConversationStore\ to track \currentConversationId\.
- Updated \AppShell.tsx\ StatusBar to dynamically display connection status (e.g., \
Ï%
Ready\, \Ï%
Offline\) based on real engine health.

**Files created or modified:**

- Created \pps/desktop/src/services/jarvisApi.ts\
- Created \pps/desktop/src/hooks/useJarvisChat.ts\
- Created \pps/desktop/src/hooks/useEngineStatus.ts\
- Modified \pps/desktop/src/stores/useConversationStore.ts\
- Modified \pps/desktop/src/components/chat/ChatView/ChatView.tsx\
- Modified \pps/desktop/src/App.tsx\
- Modified \pps/desktop/src/components/layout/AppShell.tsx\
- Modified \pps/desktop/src/stores/useAIStore.ts\ (eslint fix)
- Modified \pps/desktop/src/stores/useAppStore.ts\ (eslint fix)
- Modified \pps/desktop/src/stores/usePersonalityStore.ts\ (eslint fix)
- Updated \docs/CURRENT_STATUS.md\

**Outcome:** The desktop application is now successfully connected to the \jarvis-engine\ backend. Chat messages from the user are forwarded to the engine, and real AI responses are displayed in the \ConversationArea\. The application seamlessly updates its connection status based on the engine's health.

**Validation:** Tests passing (51/51), lint clean, and production build successful.

**Current status:** Complete and approved.


## Phase 2 - Milestone 4 (Hotfix): UI Refinements

**Date:** 2026-08-09

**Objective:** Fix UI bugs reported during Milestone 4 testing before proceeding to Milestone 5.

**Decisions made:**

- Fixed conversation area scrolling by applying \lex-1 min-h-0 overflow-y-auto\ to the \ConversationArea\ container.
- Constrained user message width to \max-w-[70%]\ and assistant message width to \max-w-[85%]\ in \MessageBubble\.
- Enforced text wrapping inside message bubbles using \whitespace-pre-wrap break-words\ to prevent overflow from long responses.

**Files created or modified:**

- Modified \pps/desktop/src/components/chat/ConversationArea/ConversationArea.tsx\
- Modified \pps/desktop/src/components/chat/MessageBubble/MessageBubble.tsx\

**Outcome:** The conversation area now scrolls correctly, allowing users to scroll back up freely while new messages auto-scroll to the bottom. Message bubbles correctly constrain their width based on role and effectively wrap long response texts.

**Validation:** Manual testing confirmed scrolling and responsiveness. Automated tests, linting, and build passed successfully.

**Current status:** Complete and approved.


## Phase 2 - Milestone 5: OpenRouter Fallback Provider

**Date:** 2026-08-09

**Objective:** Implement the OpenRouter provider as a real fallback when Ollama is offline, ensuring JARVIS automatically falls back to free OpenRouter models.

**Decisions made:**

- Replaced the OpenRouter stub with a real implementation using \httpx\ for network calls.
- Integrated OpenRouter API authentication and message formatting adhering to the OpenRouter chat completions schema.
- Added \	est_providers\ function to \	est_api.py\ to test provider statuses.
- Updated the fallback message in the \ProviderManager\ to inform the user about configuring an OpenRouter API key when no models are available.
- Created \SETUP.md\ with detailed instructions on starting the engine and configuring Ollama/OpenRouter.
- Updated \.env.example\ with OpenRouter placeholder and documentation.

**Files created or modified:**

- Modified \services/jarvis-engine/src/jarvis_engine/providers/openrouter.py\
- Modified \services/jarvis-engine/.env.example\
- Modified \services/jarvis-engine/test_api.py\
- Modified \services/jarvis-engine/src/jarvis_engine/providers/manager.py\
- Created \services/jarvis-engine/SETUP.md\
- Updated \docs/CURRENT_STATUS.md\

**Outcome:** JARVIS now seamlessly uses Ollama when available, and elegantly falls back to OpenRouter (if configured) when Ollama is unreachable. \	est_api.py\ properly tests and lists provider availabilities.

**Validation:** API tests pass successfully indicating the correct status for both Ollama and OpenRouter depending on \.env\ configurations.

**Current status:** Complete and awaiting review.


## Phase 2 - Milestone 6: Streaming Responses

**Date:** 2026-08-09

**Objective:** Implement streaming responses so words appear one by one as JARVIS thinks, matching modern chat UI patterns like ChatGPT.

**Decisions made:**

- Extracted an async \stream\ generator on the \OllamaProvider\ utilizing \httpx.AsyncClient.stream\ to stream ndjson chunks line-by-line.
- Created the \/chat/stream\ FastAPI endpoint utilizing \StreamingResponse\, returning \pplication/x-ndjson\ chunks (meta, token, done).
- Developed the frontend \sendMessageStream\ in \jarvisApi.ts\ leveraging \esponse.body.getReader()\ to decode the continuous text stream and invoke callbacks (\onToken\, \onDone\, \onError\).
- Expanded \useConversationStore.ts\ to maintain volatile \streamingMessageId\ and \streamingContent\ state during active streaming.
- Developed the \StreamingMessage\ component with a pulsing cursor to render the live stream, ensuring it's seamlessly integrated into \ConversationArea\.

**Files created or modified:**

- Modified \services/jarvis-engine/src/jarvis_engine/providers/ollama.py\
- Modified \services/jarvis-engine/src/jarvis_engine/api/routes.py\
- Modified \pps/desktop/src/services/jarvisApi.ts\
- Modified \pps/desktop/src/stores/useConversationStore.ts\
- Modified \pps/desktop/src/hooks/useJarvisChat.ts\
- Created \pps/desktop/src/components/chat/StreamingMessage/StreamingMessage.tsx\
- Created \pps/desktop/src/components/chat/StreamingMessage/StreamingMessage.test.tsx\
- Created \pps/desktop/src/components/chat/StreamingMessage/README.md\
- Modified \pps/desktop/src/components/chat/ConversationArea/ConversationArea.tsx\

**Outcome:** JARVIS answers now stream in beautifully word-by-word with a blinking cursor. The scrolling anchor automatically advances as text wraps, providing a highly premium experience.

**Validation:** Automated tests, linters, and Vite builders all passed without errors.

**Current status:** Complete and awaiting review.


## Phase 2 - Milestone 7: Long Term Memory System

**Date:** 2026-08-09

**Objective:** Implement a persistent memory system so JARVIS can learn facts, preferences, and details across sessions.

**Decisions made:**
- Extended SQLite database to include a \memories\ table with categories, importance, and access tracking.
- Created \MemoryManager\ to handle keyword search, CRUD operations, and keyword-based extraction (e.g. \
I
prefer\, \I
am\, \my
goal
is\).
- Injected retrieved memories into the \JARVIS_SYSTEM_PROMPT\ context dynamically for both \/chat\ and \/chat/stream\ routes.
- Created REST endpoints (\/memories\, \/memories/search\, \/memories/{memory_id}\) to interact with memories directly.
- Updated \models.py\ with \Memory\ and \CreateMemoryRequest\ Pydantic classes.
- Ensured graceful failing if memory extraction fails, and optimized search using SQLite \LIKE\.

**Files created or modified:**
- Modified \services/jarvis-engine/src/jarvis_engine/core/database.py\
- Created \services/jarvis-engine/src/jarvis_engine/memory/memory_manager.py\
- Modified \services/jarvis-engine/src/jarvis_engine/api/routes.py\
- Modified \services/jarvis-engine/src/jarvis_engine/core/models.py\
- Modified \services/jarvis-engine/test_api.py\

**Outcome:** JARVIS can now extract persistent facts from user prompts, store them forever in SQLite, and recall them into context automatically on subsequent requests.

**Validation:** Passed 5/5 backend tests via \	est_api.py\ including checking extraction and manual creation endpoints. Passed all 53 frontend tests successfully.

**Current status:** Complete and awaiting review.


## Phase 2 - Milestone 8: Live StatusBar + Settings Persistence

**Date:** 2026-08-09

**Objective:** Enhance the AppShell StatusBar with rich live telemetry and make the AI Provider settings fully persistent and interactive.

**Decisions made:**
- Extended \jarvisApi.ts\ to include \getMemoryCount\ and \switchProvider\ for querying and configuring engine state.
- Expanded \useAIStore\ with \memoryCount\ and \openrouterKey\.
- Updated \useEngineStatus\ to independently fetch the memory count every 60 seconds.
- Refactored \AppShell.tsx\ to dynamically render status labels (e.g., \
Ï%
Ready
·
ollama
·
llama3.2:3b\, \Ï%
Thinking...\) and dynamically fetch memory count.
- Integrated \switchProvider\ into \AIProviderSection.tsx\ so changes to provider dropdown or model input directly invoke the FastAPI backend to hot-swap models.
- Added an OpenRouter API key field (stored locally) and a 'Test Connection' UI widget in Settings.

**Files created or modified:**
- Modified \pps/desktop/src/services/jarvisApi.ts\
- Modified \pps/desktop/src/stores/useAIStore.ts\
- Modified \pps/desktop/src/hooks/useEngineStatus.ts\
- Modified \pps/desktop/src/components/layout/AppShell.tsx\
- Modified \pps/desktop/src/components/settings/AIProviderSection/AIProviderSection.tsx\

**Outcome:** The desktop interface now clearly displays what the engine is doing, how many memories it has extracted, and allows users to freely swap providers via settings with immediate effect.

**Validation:** Passed pnpm test, pnpm lint, and pnpm build.

**Current status:** Complete and awaiting review.


## Phase 2 - Milestone 9: Conversation Persistence on App Restart

**Date:** 2026-08-09

**Objective:** Automatically reload JARVIS's previous conversation upon app restart, allowing the user to seamlessly continue their session, while also offering the ability to start a fresh chat.

**Decisions made:**
- Extended the backend with \/conversations\ to fetch conversation summaries grouped with message counts.
- Bound \setConversationId\ in the Zustand store to localStorage.setItem for persistence.
- Created the \useConversationLoader\ hook, injected at the App root, which parses local storage and eagerly hydrates the zustand messages array via the backend \/conversation/{id}\ endpoint.
- Placed a 'New conversation' SquarePen button floating within the \ChatView\ when messages are present. Clicking it purges the local state, effectively returning the UI to the \IdleView\ and resetting the backend context tracker.

**Files created or modified:**
- Modified \services/jarvis-engine/src/jarvis_engine/memory/conversation.py\
- Modified \services/jarvis-engine/src/jarvis_engine/api/routes.py\
- Modified \services/jarvis-engine/test_api.py\
- Modified \pps/desktop/src/services/jarvisApi.ts\
- Modified \pps/desktop/src/stores/useConversationStore.ts\
- Created \pps/desktop/src/hooks/useConversationLoader.ts\
- Modified \pps/desktop/src/App.tsx\
- Modified \pps/desktop/src/components/chat/ChatView/ChatView.tsx\

**Outcome:** Restarting the application now properly restores the previous conversation automatically. Phase 2 AI Integration is complete.

**Validation:** Passed pnpm test, pnpm lint, and pnpm build.

**Current status:** Complete and awaiting review.


## Bug Fixes - Phase 3 Prep
**Date:** 2026-08-09
**Objective:** Fix conversation persistence and memory extraction bugs.
**Decisions made:**
- Added retry logic to useConversationLoader.ts to wait for backend.
- Relaxed memory extraction triggers in memory_manager.py.
- Improved get_relevant_memories with multi-word LIKE matching.
**Current status:** Complete.


## Phase 2 - Bug Fixes
**Date:** 2026-08-09
**Objective:** Fix conversation persistence and memory extraction bugs.
**Decisions made:**
- Added retry logic to useConversationLoader.ts to wait for backend.
- Relaxed memory extraction triggers in memory_manager.py.
- Improved get_relevant_memories with multi-word LIKE matching.
**Current status:** Complete.

## Phase 2 - Bug Fixes 2
**Date:** 2026-08-09
**Objective:** Fix duplicate memories and conversation loading bugs.
**Decisions made:**
- Added duplicate checking in save_memory().
- Replaced useConversationLoader entirely with a useRef approach and 3 second initial wait.
- Added and executed deduplication query to clean up existing duplicate memories.
**Current status:** Complete.

## Phase 2 - Bug Fixes 3
**Date:** 2026-08-09
**Objective:** Fix conversation loading on restart and OpenRouter API key submission.
**Decisions made:**
- Changed useConversationLoader to load conversation only when engine status === idle.
- Added set_openrouter_key endpoint in backend and wired it to blur event in AIProviderSection.tsx.
- Added suggestion chips for free models under AI Provider settings.
**Current status:** Complete.

## Phase 2 - Bug Fixes 4
**Date:** 2026-08-09
**Objective:** Fix localStorage issues in useConversationStore and ensure conversation ID is returned in stream.
**Decisions made:**
- Removed optional chaining from localStorage in `useConversationStore.ts`.
- Added `conversation_id` to the `done` yield in `routes.py` `/chat/stream`.
- Added fallback to `jarvisApi.ts` `onDone` callback.
**Current status:** Complete.

## Phase 3 - Milestone 1: Web Search
**Date:** 2026-08-09
**Objective:** Add DuckDuckGo web search capability to JARVIS.
**Decisions made:**
- Installed `duckduckgo-search` and `httpx`.
- Created `web_search.py` for performing queries and formatting results.
- Created `search_detector.py` to identify search intent using heuristics and keywords.
- Added a new `/search` endpoint to the FastAPI app.
- Injected search results directly into the `system` message prompt before calling the LLM in `/chat` and `/chat/stream` endpoints.
**Current status:** Complete. Tests pass successfully.

## Phase 3 - Milestone 2: Complete UI Overhaul
**Date:** 2026-08-10
**Objective:** Rebuild the JARVIS UI to match the advanced HUD concept.
**Decisions made:**
- Implemented 12-step plan to integrate the new design system (fonts, colors, background).
- Created GraphCanvas for background node physics, Orb for AI status, Topbar for metrics, Dock for navigation, and Panel columns.
- Preserved Chat functionality via ChatShell and history via ConversationPanel.
- Renamed old AppShell, AppHeader, ChatView and rewired App.tsx to use the new HUD layout.
**Current status:** Complete. All 53 tests pass successfully.

## Phase 3 - Milestone 2: UI Overhaul Fixes
**Date:** 2026-08-11
**Objective:** Fix UI layout, HUD styling, graph physics, and add real system stats.
**Decisions made:**
- Migrated ChatShell to use Tailwind classes directly without separate CSS.
- Adjusted RightColumn layout, Orb size, and GraphCanvas physics (spread, node sizes, labels).
- Integrated sysinfo into Tauri lib.rs and LeftColumn for live system metrics.
**Current status:** Complete. Tests and build pass successfully.

## 2026-08-11: Phase 3 - Milestone 2 UI Fixes Round 3
### Issues Fixed
- **FIX 1:** Changed `GraphCanvas` to start at Level 1 (Hubs visible) instead of Level 0 (Closed) by default.
- **FIX 2:** Implemented orbiting leaf nodes around their respective hubs using `Math.PI * 2 / numLeaves` and orbit physics loop. Nodes are smaller (5px) and labels are JetBrains Mono 9px.
- **FIX 3:** Adjusted `ChatShell` sizing logic (Max height 60vh - 120px, Min height 200px) and width (680px) and updated scrolling/fading logic to show latest messages nicely.
- **FIX 4:** Rebuilt `RightColumn` flex layout for better real-estate use. Adjusted Filter panel padding, fixed Orb card padding, and aligned Graph stats horizontally.
- **FIX 5:** Updated `ConversationPanel` click handler to actually load messages using `clearConversation()` and mapping fetched history using `addMessage()`.
- **FIX 6:** Enhanced `get_conversations` in `conversation.py` to automatically generate titles from the first user message if the title is blank or "New Conversation".
- **FIX 7:** Upgraded Tauri backend (`lib.rs`) to retrieve actual CPU, memory, and dual GPU (discrete & integrated) system stats via `sysinfo`. UI in `LeftColumn.tsx` now successfully displays both GPU load states accurately.

### Validation
- Tests: Re-ran `pnpm test` (53/53 passed).
- Linting: Re-ran `pnpm lint` successfully.
- Build: Verified successful compilation in `pnpm build`.
**Current status:** Complete. Tests and build pass successfully.

## 2026-08-11: Phase 3 - Milestone 2 Final UI Fixes
### Issues Fixed
- **FIX 1:** Adjusted `GraphCanvas` to display a tight cluster of nodes at Level 0. Toggling between Level 0 and 1 now scales the cluster radius.
- **FIX 2:** Added a `chatMode` toggle in `Dock` to transition the app into a full-center chat view (`ChatFullView`), hiding the graph completely for focused conversations.
- **FIX 3:** Implemented a hover effect in `GraphCanvas` that reduces the orbit/rotation speed of nodes to 15% when the user's cursor is near any node and changes the cursor to a pointer.

### Validation
- Tests: Re-ran `pnpm test`.
- Linting: Re-ran `pnpm lint`.
- Build: Currently running `pnpm build`.

## Phase 3 - Milestone 3: Tavily Search + Sources UI
**Date:** 2026-08-14
**Objective:** Upgrade backend search engine to Tavily and expose search metadata in the HUD.
**Decisions made:**
- Configured backend with `tavily-python` and updated `web_search.py` to use a tiered search approach (Tavily with DuckDuckGo fallback).
- Passed robust search metadata (`search_performed`, `search_query`, `sources`) down through the SSE stream via a new `meta` chunk.
- Parsed metadata in the React frontend (`jarvisApi.ts`, `useJarvisChat.ts`).
- Displayed `SearchBadge` above JARVIS's messages when a search query is utilized.
- Rendered `SourcesList` below JARVIS's message with a list of interactive citations.
- Configured Tauri `shell` plugin and `shell:allow-open` capability to safely launch external URLs in the user's default browser.
**Current status:** Complete. Backend tests, frontend tests, and frontend build successfully pass.

## Phase 3 - Milestone 4: [UI_ACTION] Protocol
**Date:** 2026-08-14
**Objective:** Enable the AI to trigger frontend UI commands via special response tags.
**Decisions made:**
- Taught JARVIS a `[UI_ACTION]` protocol using an injected system prompt instructions.
- Implemented `uiActionParser.ts` to cleanly extract these tags from text (including streaming partial tags).
- Implemented `uiActionExecutor.ts` to execute extracted UI actions by mutating the Zustand global store.
- Updated `useJarvisChat.ts` to seamlessly parse tags, strip them, and queue actions so raw tags are hidden during SSE streams and completed messages.
- Updated `GraphCanvas.tsx` to deeply integrate its internal rendering state (`selectedHub`, `graphOpen`) with the global `graphLevel` from the store, enabling two-way reactive state tracking and synchronization.
- **Milestone 4 additions:** Removed auto chat mode switch from `ChatShell.tsx`, allowing users to stay in graph mode while JARVIS executes UI actions in the background.
- Added `ActionFeedback` to the Orb and updated `LeftColumn` Inspector to log UI actions visually when in graph mode without disrupting the screen.
- **Bug Fixes:**
  - Ensured `GraphCanvas.tsx` properly clears `activeHub` when switching away from Level 2 so same-hub clicks trigger again properly, and added cleanup timeout to `uiActionExecutor.ts`.
  - Upgraded explicit transition in `GraphCanvas.tsx` drill-down (`graph_open_hub`) to handle collapsed Level 0, going to Level 1, waiting 600ms, and then proceeding to Level 2.
  - Re-synced `GraphCanvas.tsx` logic so it gracefully handles `graphLevel === 0` collapse.
**Current status:** Complete. Backend tests, frontend unit tests (`parseUIActions`, `ActionFeedback` specifically), and UI build completed successfully.

## Phase 3 - Milestone 5: Background Search
**Date:** 2026-08-15
**Objective:** Parallelize AI streaming and web search to eliminate search delay.
**Decisions made:**
- Refactored `api/routes.py` `POST /chat/stream` to initiate `search_web` asynchronously alongside `provider_manager.stream` using `asyncio.create_task`.
- Passed the `meta` chunk immediately with an empty sources array, then yielded token chunks.
- Awaited the background search task using `asyncio.wait_for` after token streaming completed.
- Saved search results as a hidden system message (`role: "system"`) directly into the SQLite database to provide context for the next follow-up message without exposing it to the UI.
- Updated `POST /chat` to run `search_web` and `provider_manager.chat` using `asyncio.gather`.
- Sent final search sources securely in the `done` chunk.
- Adjusted React frontend `jarvisApi.ts` and `useJarvisChat.ts` to properly consume `sources` from the `done` chunk instead of relying strictly on the `meta` chunk reference.
- Filtered `role: "system"` messages out of the `get_conversation_messages` SQL query so they don't break the frontend UI.
- Added `test_parallel_search()` timing benchmark to `test_api.py`.
- **Bug Fixes:**
  - Fixed an issue where the UI_ACTION protocol stopped working after a web search. The background search saved context as a `role: "system"` message in the database, which was filtered out in `get_conversation_messages`, causing the context to be lost for the backend.
  - Modified `get_conversation_messages` to retrieve system messages from the database, and `get_conversation_endpoint` to filter them out before returning to the frontend UI.
  - Updated `routes.py` to correctly extract system messages from the conversation history, concatenate their contents, and append them directly to the main `JARVIS_SYSTEM_PROMPT` to prevent the LLM from dropping the system prompt and UI action rules mid-conversation.
  - Added additional examples (`[UI_ACTION:chat_mode_on]`, `[UI_ACTION:graph_collapse]`) to the `UI_ACTION_INSTRUCTION` in `routes.py` to improve LLaMA 3.2 3B's reliability.
  - Refactored `useJarvisChat.ts` `onDone` callback to correctly parse UI actions *before* building the message and storing it in state.
**Current status:** Complete. Parallel execution measured at ~9.6s. Frontend and backend tests pass. Build successful.

## Phase 4 - Additional Providers
**Milestone 1 - Groq Provider**
**Date:** 2026-08-16
**Objective:** Add support for Groq API to provide blazing-fast inference using Llama 3.3 70B models.
**Decisions made:**
- Created `GroqProvider` implementing `BaseProvider` to interface with the Groq API using the official Python SDK.
- Updated `ProviderManager` to include `GroqProvider` as Priority 2, between OpenRouter and Ollama.
- Expanded configuration in `config.py` and `.env.example` with `GROQ_API_KEY` and `GROQ_MODEL` settings.
- Adjusted React frontend settings UI (`AIProviderSection.tsx`, `useAIStore.ts`) to offer Groq as a selectable provider with corresponding Llama 3 models.
**Current status:** Complete. API tests confirm successful integration, and frontend build is successful.

## Bug Audit & Fixes
**Date:** 2026-08-17

**Objective:** Address critical bugs identified during the desktop app audit.

**Decisions made:**
- Fix search race condition: Enforce sequential search resolution before yielding to AI generation, so search results are injected into the context correctly.
- Offload synchronous web search API calls (Tavily, DDG) to `asyncio.to_thread` to unblock the main event loop.
- Rewrite `search_detector.py` entirely using regexes to lower false positives.
- Disable "New Chat" button during streaming to prevent state corruption.
- Fix memory leak and undefined behaviors in `setTimeout` across multiple hooks.
- Fix Tauri security risks: enabled CSP, handled Mutex poisoning gracefully, and bounded integer ranges.
- Added 8 new search detection patterns for company news and update queries.

**Files created or modified:**
- `routes.py`, `web_search.py`, `search_detector.py`
- `ChatShell.tsx`, `ChatFullView.tsx`, `useJarvisChat.ts`, `useAppStore.ts`, `jarvisApi.ts`, `useConversationStore.ts`
- `tauri.conf.json`, `lib.rs`
- `CURRENT_STATUS.md`, `DEVELOPMENT_LOG.md`

**Outcome:** Search features and desktop application stability vastly improved.

---

## Phase 4 - Milestone 1: Desktop Automation

**Date:** 2026-08-17

**Objective:** Implement Dynamic Command Execution System.

**Decisions made:**
- Add powershell and dynamic app finding commands in lib.rs.
- Generate JSON automation schemas in Groq API within routes.py.
- Add systemApi.ts bindings.
- Intercept UI actions for automation commands and store pending commands.
- Add real battery and disk usage components to LeftColumn.tsx.

**Outcome:** JARVIS can now control the Windows PC dynamically and safely.

**Status:** Complete and approved.

---

## Phase 4 - Desktop Automation Fixes

**Date:** 2026-08-17

**Objective:** Optimize automation context and fallback logic.

**Decisions made:**
- Changed the automation context injection from a long detailed prompt to a concise string of just the required UI_ACTION tags (max 300 characters). This avoids context limit errors on Gemini and saves Groq tokens.
- Applied the shortened automation context format identically to both the `/chat/stream` and the `/chat` endpoints.
- Updated provider selection logic when `automation_results` is present: prioritize structured-response-friendly models (OpenRouter, Groq) over others.

**Files created or modified:**
- Modified `routes.py`

**Outcome:** Automation prompts are highly efficient, API tokens are saved, and the engine correctly falls back to models better suited for structured JSON and short text.

**Status:** Complete and tested.

---

## Phase 4 - Desktop Automation Fixes

**Date:** 2026-08-17

**Objective:** Prevent duplicate windows when opening URLs.

**Decisions made:**
- Added a `CRITICAL DEDUPLICATION RULE` to `COMMAND_GENERATION_PROMPT` so the LLM doesn't emit both `OPEN_APP` and `OPEN_URL` for the same browser in a single request.
- Implemented `deduplicate_actions()` in `routes.py` to filter out redundant `OPEN_APP` commands if an `OPEN_URL` action exists for the same browser (handling aliases like "firefox", "mozilla").
- Called `deduplicate_actions()` within `generate_automation_command()` after parsing the LLM output.

**Files created or modified:**
- Modified `routes.py`

**Outcome:** Requests like "open firefox and search youtube" now open exactly one window with the requested URL, while "open firefox and notepad" still opens two separate apps correctly.

**Status:** Complete and tested.

## Phase 4 - Milestone 2: Foreground Search

**Date:** 2026-08-17

**Objective:** Add foreground search detection and URL building to route the user's intent to visually present search results in a browser rather than background processing.

**Decisions made:**
- Added `needs_foreground_search` to detect commands asking to "show me", "search on youtube", or open common websites.
- Implemented `build_foreground_url` to construct search query strings and URLs for YouTube, Google, and standard sites.
- Integrated detection inside `chat_endpoint` and `chat_stream_endpoint`, injecting a `[UI_ACTION:open_url:browser:url]` command into the system message context when foreground search is needed, effectively overriding background web search.

**Files created or modified:**
- Modified `routes.py`
- Created `test_foreground.py`

**Outcome:** Background search handles general conversational knowledge, while explicit visual requests open Firefox directly.

**Status:** Complete and tested.

## Phase 4 - Milestone 3: File System Operations

**Date:** 2026-08-17

**Objective:** Enable JARVIS to interact with the local file system using the Rust/Tauri backend. Features include directory listing, file reading, file/folder deletion (with user confirmation), and file explorer integration.

**Decisions made:**
- Added standard `std::fs` operations to `lib.rs` and registered them as Tauri commands.
- Implemented shortcuts in paths (`~` and `%DESKTOP%`) for user convenience.
- Limited file reads to 100KB and restricted reads to specific safe extensions (`txt`, `md`, `json`, etc.) to ensure security and prevent memory exhaustion.
- Enforced a `REQUIRES_CONFIRMATION` flag for all destructive file operations (deletion).
- Refined the prompt context in `routes.py` to support natural language queries mapped to the new filesystem `UI_ACTION` tags.
- Hooked the frontend to these API commands via `uiActionExecutor.ts` and `systemApi.ts`, presenting the results immediately in the chat interface.

**Files created or modified:**
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src/services/systemApi.ts`
- `apps/desktop/src/utils/uiActionExecutor.ts`
- `services/jarvis-engine/src/jarvis_engine/api/routes.py`
- `docs/CURRENT_STATUS.md`

**Outcome:** JARVIS can now seamlessly interpret file system instructions and safely execute operations on the user's local filesystem with full UI feedback.

**Status:** Complete and tested.

## Phase 4 - Milestone 3: File System Operations (Fixes)

**Date:** 2026-08-17

**Objective:** Fix command generation ambiguities where JARVIS confused Graph UI file requests with actual file system commands.

**Decisions made:**
- Added explicit "CRITICAL FILE SYSTEM RULES" to `COMMAND_GENERATION_PROMPT` to teach the AI to map "show my desktop/downloads" strictly to `list_dir` rather than `graph_open_hub`.
- Updated `get_automation_context_str` in `routes.py` to parse `SYSTEM_QUERY` for `list_dir` and `FILE_OP` for `create_folder`, `delete_file`, `open_file`, and `show_explorer`.
- Replaced the string slice truncation limit for the injected automation context to preserve complete command arrays.
- Expanded the automation triggers in `needs_automation()` with targeted file system phrases.

**Files created or modified:**
- `services/jarvis-engine/src/jarvis_engine/api/routes.py`

**Outcome:** File system commands accurately reflect system queries rather than UI toggles, providing correct functional responses in chat.

## Phase 4 - Milestone 3: File System Operations (Implementation Fixes)

**Date:** 2026-08-17

**Objective:** Implement direct detection of file system operations to bypass LLM generation hallucinations entirely for specific user commands.

**Decisions made:**
- Implemented `is_file_system_command` in `routes.py` to intercept filesystem commands based on robust regex and substring checks.
- Hooked this check at the very beginning of the `/chat` and `/chat/stream` endpoints to prevent `needs_automation` and LLM prompting for file queries.
- Updated `uiActionExecutor.ts` in the frontend to gracefully handle `confirm_action` payloads formatted as `action_type:path`.
- Modified the confirmation action logic in `useJarvisChat.ts` to execute `systemApi.deleteFile` directly instead of passing it to PowerShell when the user confirms a `delete_file` action.
- Ran `pnpm build` to compile the frontend changes.

**Files created or modified:**
- `services/jarvis-engine/src/jarvis_engine/api/routes.py`
- `apps/desktop/src/utils/uiActionExecutor.ts`
- `apps/desktop/src/hooks/useJarvisChat.ts`
- `docs/DEVELOPMENT_LOG.md`

**Outcome:** File system operations now bypass the LLM entirely, instantly returning explicit actions to the frontend. The `delete_file` process safely requests user confirmation and invokes the Rust backend properly.

**Status:** Implementation complete. Ready for manual validation.

---

## Phase 4 - Milestone 3: File System Operations (Context Optimization & UX Improvements)

**Date:** 2026-08-17

**Objective:** Optimize file system command processing to reduce context size for providers with token limits, preserve folder name case, handle "already exists" gracefully, and improve file listing UI.

**Decisions made:**

1. **Context Minimization for File Commands:**
   - When `is_file_system_command()` detects a file system operation, override the full message list with minimal context containing only:
     - Shortened system prompt (first 500 characters)
     - File system command context
     - Current user message
   - Skip conversation history, memory context, and search results for file commands as they're deterministic operations that don't require conversation context
   - Apply optimization to both `/chat` and `/chat/stream` endpoints
   - Skip complex provider selection logic for file commands; use first available provider

2. **Preserve Folder Name Case:**
   - Modified `is_file_system_command()` regex to use original `message` instead of `msg_lower` when extracting folder names
   - Added `re.IGNORECASE` flag to match triggers case-insensitively while preserving the user's intended capitalization
   - Normalize only the `location` parameter (Desktop/Downloads) to lowercase for path matching

3. **Handle "Already Exists" Gracefully:**
   - Updated `create_folder` command in `lib.rs` to check if folder exists before attempting creation
   - Return success message "Folder already exists: {path}" instead of error when folder already exists
   - Prevents unnecessary error messages and provides better UX

4. **Improved File Listing Display:**
   - Enhanced `list_dir` case in `uiActionExecutor.ts` with cleaner formatting:
     - Bold path header with folder emoji
     - Summary line showing folder/file counts with bullet separator
     - Display up to 10 folders and 15 files (increased from 5/10)
     - Show file sizes in human-readable format (MB/KB/B)
     - Add overflow indicator when total items exceed 25
     - More professional feedback message with "sir" suffix

**Files created or modified:**
- `services/jarvis-engine/src/jarvis_engine/api/routes.py`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src/utils/uiActionExecutor.ts`
- `docs/DEVELOPMENT_LOG.md`

**Outcome:** File system commands now work reliably with all AI providers regardless of context limits. Folder creation preserves user-intended capitalization. File listings are more informative and visually organized with size information.

**Status:** Complete. Builds successful (cargo build: 1.12s, pnpm build: 10.29s).

---

## Phase 4 - Milestone 4: Safety Layer

**Date:** 2026-08-17

**Objective:** Implement a comprehensive safety system that requires user confirmation before executing any destructive or irreversible action, protecting the user from accidental data loss or system changes.

**Decisions made:**

1. **Destructive Action Detection:**
   - Added `is_destructive_action()` function in `routes.py` with pattern matching for dangerous keywords: delete, remove, kill, terminate, shutdown, restart, format, clear, uninstall, wipe, erase
   - Integrated safety check with file system command detection to automatically flag operations requiring confirmation
   - Enhanced confirmation context messages to explicitly state what will be affected and require clear YES/NO response

2. **Confirmation UI System:**
   - Created `ConfirmationButtons` component with HUD-styled Confirm (red) and Cancel (cyan) buttons
   - Buttons appear automatically when `pendingCommand` is set in app store
   - Event-based communication using custom `jarvis-confirm` events to decouple UI from chat logic
   - Integrated into both `ChatFullView` and `ChatShell` for consistent UX

3. **Confirmation Event Flow:**
   - Added event listener in `useJarvisChat` hook to handle confirmation responses
   - "Yes" response executes pending command through existing confirmation flow
   - "No/Cancel" response clears pending command and adds cancellation message to chat
   - Maintains existing delete_file confirmation logic while extending to all destructive actions

4. **System Control Commands:**
   - Implemented `shutdown_computer()` command in `lib.rs` with mandatory confirmation and 30-second grace period
   - Implemented `cancel_shutdown()` command to abort scheduled shutdowns
   - Implemented `restart_computer()` command with mandatory confirmation and 30-second delay
   - All system control commands return descriptive messages and require confirmation flag

5. **Safety Rules Documentation:**
   - Added comprehensive "SAFETY RULES - ALWAYS FOLLOW" section to `COMMAND_GENERATION_PROMPT`
   - Clearly categorized safe actions (open apps, create folders, list files, lock screen)
   - Clearly categorized destructive actions (delete, shutdown, kill process, format, uninstall)
   - Mandated `requires_confirmation: true` for all destructive operations

**Files created or modified:**
- `services/jarvis-engine/src/jarvis_engine/api/routes.py` - Added safety classifier and enhanced confirmation flow
- `apps/desktop/src/components/chat/ConfirmationButtons/ConfirmationButtons.tsx` - New confirmation UI component
- `apps/desktop/src/hooks/useJarvisChat.ts` - Added confirmation event listener
- `apps/desktop/src/components/chat/ChatFullView/ChatFullView.tsx` - Integrated ConfirmationButtons
- `apps/desktop/src/components/chat/ChatShell/ChatShell.tsx` - Integrated ConfirmationButtons
- `apps/desktop/src-tauri/src/lib.rs` - Added shutdown/restart commands with safety checks
- `docs/CURRENT_STATUS.md` - Updated to reflect Milestone 4 completion
- `docs/DEVELOPMENT_LOG.md` - Documented Milestone 4 implementation

**Outcome:** JARVIS now features a robust safety layer that prevents accidental execution of destructive commands. All file deletions, system shutdowns/restarts, and process terminations require explicit user confirmation through a clean HUD-styled UI. The system provides clear feedback about what will be affected and gives users the option to cancel any dangerous operation.

**Status:** Complete. Builds successful (cargo build: 1.26s, pnpm build: 9.86s). Ready for Milestone 5.
