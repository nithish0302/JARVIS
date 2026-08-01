# JARVIS Design Tokens

Version: 1.0.0

Status: Active

---

## Purpose

This document is the canonical specification for JARVIS design tokens.
`apps/desktop/src/styles/tokens.css` must implement these semantic values.
Components consume tokens rather than introducing literal visual values.

JARVIS currently supports the dark theme only. The `:root` and
`[data-theme="dark"]` blocks intentionally contain the same values so a future
approved light palette can replace semantic values without changing component
code.

---

## Colors

| Token | Value or alias | Purpose |
|---|---|---|
| `--color-background` | `#05080F` | Main application background. |
| `--color-background-secondary` | `#0B1220` | Panels, cards, and sidebars. |
| `--color-surface` | `#111827` | Containers, settings, and conversation blocks. |
| `--color-surface-raised` | `var(--color-surface)` | Future elevated surfaces. |
| `--color-accent` | `#00D4FF` | Primary interactive and active state. |
| `--color-accent-hover` | `#38BDF8` | Hover, selection, and indicator state. |
| `--color-highlight` | `#4FE6FF` | Reserved for AI Core, active microphone, and important highlights. |
| `--color-success` | `#22C55E` | Success state. |
| `--color-warning` | `#FACC15` | Warning state. |
| `--color-error` | `#EF4444` | Error state. |
| `--color-text-primary` | `CanvasText` | Primary readable text. |
| `--color-text-secondary` | derived from `CanvasText` | Secondary readable text. |
| `--color-text-muted` | `var(--color-text-secondary)` | De-emphasized text. |
| `--color-border` | semantic derived value | Standard border. |
| `--color-border-subtle` | semantic derived value | Low-emphasis border. |
| `--color-border-focus` | `var(--color-accent)` | Keyboard and focused-field border. |

No additional palette hue may be introduced without updating this document.

## Typography

| Token | Value |
|---|---|
| `--font-family-sans` | `Inter, system-ui, sans-serif` |
| `--font-family-mono` | `SFMono-Regular, Consolas, Liberation Mono, monospace` |
| `--font-size-caption` | `0.75rem` |
| `--font-size-sm` | `0.875rem` |
| `--font-size-body` | `1rem` |
| `--font-size-section` | `1.25rem` |
| `--font-size-page` | `1.5rem` |
| `--font-size-display` | `2rem` |
| `--line-height-caption` | `1rem` |
| `--line-height-sm` | `1.25rem` |
| `--line-height-body` | `1.5rem` |
| `--line-height-section` | `1.75rem` |
| `--line-height-page` | `2rem` |
| `--line-height-display` | `2.5rem` |
| `--font-weight-regular` | `400` |
| `--font-weight-medium` | `500` |
| `--font-weight-semibold` | `600` |

The monospace token is reserved for future diagnostics and developer-facing UI.

## Spacing

| Token | Value |
|---|---:|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-12` | 48px |
| `--space-16` | 64px |

## Radius and borders

| Token | Value | Purpose |
|---|---:|---|
| `--radius-sm` | 12px | Buttons and inputs. |
| `--radius-md` | 16px | Cards. |
| `--radius-lg` | 20px | Panels. |
| `--radius-full` | 9999px | Future badges, chips, voice controls, and status indicators. |
| `--border-width` | 1px | Standard border width. |

## Shadows, blur, and elevation

| Token | Value | Intended use |
|---|---|---|
| `--shadow-none` | `none` | Base content. |
| `--shadow-sm` | `0 4px 12px rgb(5 8 15 / 25%)` | Standard raised card or surface. |
| `--shadow-md` | `0 12px 24px rgb(5 8 15 / 35%)` | Temporary elevated surface. |
| `--shadow-lg` | `0 16px 32px rgb(5 8 15 / 40%)` | Future high-elevation surface; not for routine cards. |
| `--blur-sm` | 8px | Subtle future glass treatment. |
| `--blur-md` | 16px | Standard future glass treatment. |
| `--blur-lg` | 24px | Future high-emphasis glass treatment. |

Glow is distinct from elevation and must remain restrained.

| Token | Value |
|---|---|
| `--glow-sm` | `0 0 16px rgb(79 230 255 / 25%)` |
| `--glow-md` | `0 0 32px rgb(79 230 255 / 35%)` |

## Icons

| Token | Value |
|---|---:|
| `--icon-size-sm` | 16px |
| `--icon-size-md` | 20px |
| `--icon-size-lg` | 24px |

These tokens are reserved for future Lucide React outline icons.

## Motion and opacity

| Token | Value | Purpose |
|---|---|---|
| `--duration-fast` | 150ms | Fast interaction. |
| `--duration-normal` | 250ms | Normal interaction. |
| `--duration-slow` | 400ms | Large transition. |
| `--ease-standard` | `ease-out` | Default interaction easing. |
| `--ease-emphasized` | `ease-in-out` | Deliberate state transition. |
| `--ease-sharp` | `cubic-bezier(0.4, 0, 0.6, 1)` | Future sharp transition. |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Future spring-like transition. |
| `--opacity-disabled` | `0.5` | Disabled control. |
| `--opacity-hover` | `0.9` | Future opacity-based hover treatment. |
| `--opacity-overlay` | `0.64` | Future overlay backdrop. |
| `--scale-active` | `0.98` | Active control feedback. |

Tokens do not authorize animation by themselves. Continuous animation remains
reserved for the AI Core as defined by the design system.

## Focus and layering

| Token | Value or alias | Purpose |
|---|---|---|
| `--focus-ring-color` | `var(--color-border-focus)` | Focus outline color. |
| `--focus-ring-width` | 2px | Focus outline width. |
| `--focus-ring-offset` | 2px | Focus outline offset. |
| `--z-base` | 0 | Base content. |
| `--z-header` | 10 | Persistent header. |
| `--z-overlay` | 20 | Future overlay. |
| `--z-modal` | 30 | Future modal. |
| `--z-toast` | 40 | Future notification. |

Use semantic layer tokens only; do not introduce arbitrary z-index values.
