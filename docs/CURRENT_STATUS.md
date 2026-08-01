# JARVIS Current Status

Last updated: 2026-08-01

## Current phase

**Phase 0 - Foundation**

The project is establishing the desktop application foundation before Phase 1
user-interface features begin.

## Current milestone

**Milestone 6B - Base UI Component Library: Extended Primitives**

Status: **Implementation complete; awaiting review.**

The second implementation half of the permanent base UI component library is
complete. It adds the remaining approved form, loading, and status primitives
without application features or business logic.

Validation passed: unit tests, lint, and the production build. Static review
found no literal visual values in Milestone 6B component source, and each
approved component has its required README and test file.

The canonical design and token specifications document the approved narrow
Spinner exception to the AI Core-only continuous-animation rule.

## Completed milestones

| Milestone | Status | Result |
|---|---|---|
| Phase 0 - Milestone 1: Tauri template cleanup | Complete | Removed template greeting/opener behavior and renamed the canonical desktop app to JARVIS. |
| Phase 0 - Milestone 2: Design foundation | Complete | Added semantic token and global-style foundations. |
| Phase 0 - Milestone 3: Reusable UI primitives | Complete | Added Button, IconButton, Input, Card, StatusIndicator, and the shared `cn` utility. |
| Phase 0 - Milestone 3 refinement | Complete | Added documented input focus and button interaction states using semantic tokens. |
| Phase 0 - Milestone 4: Application shell | Complete | Added static layout structure, semantic layering, and single-main-scroll ownership without feature UI. |
| Phase 0 - Milestone 5: Design System Foundation | Complete | Added the canonical semantic design-token specification and expanded the token implementation. |
| Phase 0 - Milestone 6A: Base UI Component Library - Core Primitives | Complete | Added Button, IconButton, Card, Panel, Badge, Divider, Field, and Input in self-contained component folders. |
| Phase 0 - Milestone 6B: Base UI Component Library - Extended Primitives | Complete; awaiting review | Added Textarea, Select, Checkbox, Switch, Spinner, Skeleton, and StatusIndicator in self-contained component folders. |

## Pending milestone

**Milestone 6B review**

Awaiting review. No further implementation milestone should begin until this
milestone is accepted.

## Next planned milestone

The next implementation milestone has not yet been formally defined. The
roadmap places Phase 1 - User Interface next, but its milestone breakdown has
not been reconstructed from the available project documentation.


## Current technology stack

### Canonical desktop application

- Tauri v2 with Rust backend
- React 19
- TypeScript
- Vite
- Tailwind CSS v4 with PostCSS
- Framer Motion
- clsx
- Vitest, Testing Library, ESLint, and Prettier development tooling

### Documented stack not currently used by the canonical desktop manifest

- Zustand is an accepted architecture decision for future global state, but it
  is not currently listed in `apps/desktop/package.json` and no store exists.
- Lucide React is specified by the design system, but it is not currently
  listed in `apps/desktop/package.json` and no icon component is rendered.

### Present but not yet documented as active product usage

- `three`, `@react-three/fiber`, and `@react-three/drei` are present in the
  canonical desktop package manifest. No current JARVIS feature or project
  document establishes their use.

## Active architecture decisions

| ADR | Decision | Status |
|---|---|---|
| 0001 | Use Tauri v2 instead of Electron. | Accepted and active. |
| 0002 | Use Zustand for global state; retain React state for local component state. | Accepted and active for future state needs. |
| 0003 | Use a 70% modern desktop / 30% Iron Man-inspired design language. | Accepted and active. |
| 0004 | Keep AI providers independent through an abstraction layer. | Accepted and active for future AI work. |

## Tracking maintenance

- Update this document after every approved milestone so it reflects the latest
  verified repository state.
- Append, rather than rewrite, milestone history in `DEVELOPMENT_LOG.md`.
