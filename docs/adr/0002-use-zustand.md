# ADR 0002

## Title

Use Zustand for Global State

---

## Status

Accepted

---

## Context

The application requires lightweight global state management.

Possible solutions included:

- Redux
- Context API
- Zustand

---

## Decision

Use Zustand.

---

## Reasons

- Simple API
- Minimal boilerplate
- Excellent TypeScript support
- Small bundle size
- Easy scalability

---

## Consequences

Global state will remain small and organized.

React local state will continue handling component-specific logic.
