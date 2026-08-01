# JARVIS Development Rules

Version: 0.1.0

Status: Active

---

# Purpose

This document defines the engineering standards for the JARVIS project.

Every developer and every AI assistant must follow these rules.

These rules exist to maintain consistency, scalability, readability, and long-term maintainability.

---

# Core Principles

Every line of code should prioritize:

- Readability
- Maintainability
- Scalability
- Reusability
- Performance
- Simplicity

Avoid shortcuts that create technical debt.

---

# General Rules

Always:

- Use TypeScript.
- Write strongly typed code.
- Prefer explicit code over clever code.
- Keep functions small and focused.
- Keep components focused on a single responsibility.
- Use meaningful variable names.
- Write self-documenting code.

Never:

- Use "any" unless absolutely unavoidable.
- Leave commented-out code.
- Commit debugging code.
- Create unnecessary files.
- Duplicate logic.

---

# React Rules

Every component should have one responsibility.

Example:

Good

```
ChatInput.tsx
ChatMessage.tsx
ChatWindow.tsx
```

Avoid

```
Chat.tsx
```

that contains everything.

---

# Component Rules

Components should be:

Reusable

Composable

Small

Easy to test

Avoid components larger than necessary.

Split large components into logical child components.

---

# File Naming

Components

```
PascalCase.tsx
```

Examples

```
ChatInput.tsx

AiCore.tsx

SettingsPanel.tsx
```

Hooks

```
useSomething.ts
```

Example

```
useSpeechRecognition.ts
```

Utilities

```
camelCase.ts
```

Example

```
formatTime.ts
```

Types

```
types.ts
```

or

```
chat.types.ts
```

---

# Folder Rules

Each folder should have a single responsibility.

Never place unrelated files together.

Examples

Good

```
components/chat

components/layout

components/status
```

Avoid

```
components/misc
```

---

# State Management

Global State

Use Zustand.

Examples

- Theme
- Settings
- AI State
- Conversation

Local State

Use React state.

Avoid placing local UI state inside Zustand.

---

# Styling Rules

Use Tailwind CSS.

Avoid inline styles.

Avoid large CSS files.

Use reusable utility classes.

Create reusable UI components instead of repeating styles.

---

# Animation Rules

Use Framer Motion.

Animations must have purpose.

Allowed

- Fade
- Scale
- Rotate
- Slide
- Pulse

Avoid decorative animations.

---

# Rust Rules

Rust should handle:

- Native APIs
- File System
- Automation
- Performance intensive work
- OS interaction

Rust should never contain frontend presentation logic.

---

# React ↔ Rust Communication

Always communicate through Tauri commands.

Never bypass the Tauri architecture.

---

# Error Handling

Every operation should return meaningful errors.

Frontend

Show user-friendly messages.

Backend

Log technical details.

Never silently ignore errors.

---

# Logging

Development

Useful logs are allowed.

Production

Remove unnecessary logs.

Never expose secrets.

---

# Security

Never hardcode:

- API Keys
- Passwords
- Tokens

Use environment variables.

Validate external input.

Confirm dangerous actions before execution.

---

# Performance

Avoid unnecessary renders.

Use lazy loading when appropriate.

Memoize only when it provides measurable benefit.

Keep components lightweight.

---

# Dependencies

Before adding a dependency ask:

Do we actually need it?

Prefer existing solutions before introducing new libraries.

Every dependency increases maintenance cost.

---

# Documentation

Every major architectural decision must be documented.

Complex code should be explained.

Keep documentation synchronized with implementation.

---

# Git Rules

Commit frequently.

Each commit should represent one logical change.

Good commit messages

```
feat: add AI Core component

fix: improve voice state handling

refactor: split chat into reusable components
```

Avoid

```
update

changes

fixed stuff
```

---

# AI Generation Rules

When using AI assistants:

Never ask the AI to build the whole application.

Instead:

Build one feature.

Review it.

Improve it.

Commit it.

Repeat.

AI-generated code must always be reviewed before merging.

---

# Code Review Checklist

Before completing any feature ask:

- Is the code readable?
- Is it reusable?
- Is it scalable?
- Does it follow the architecture?
- Does it follow the design system?
- Is there duplicated logic?
- Can this be simplified?

If the answer is "No" to any question, improve the implementation before continuing.

---

# Final Rule

Quality is more important than speed.

The objective is not to finish quickly.

The objective is to build a desktop AI assistant that remains maintainable, extensible, and enjoyable to work on for years.
