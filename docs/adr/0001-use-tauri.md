# ADR 0001

## Title

Use Tauri instead of Electron

---

## Status

Accepted

---

## Context

The JARVIS project requires a desktop application with excellent performance, low memory usage, strong security, and native operating system integration.

Several desktop frameworks were evaluated.

Examples:

- Electron
- Tauri

---

## Decision

The project will use Tauri v2.

---

## Reasons

- Lower memory usage
- Smaller application size
- Native Rust backend
- Better security model
- Excellent Windows integration
- Strong future support

---

## Consequences

Frontend and backend remain separated.

React focuses on UI.

Rust handles operating system interaction.

This architecture supports future automation features.
