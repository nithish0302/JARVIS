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
