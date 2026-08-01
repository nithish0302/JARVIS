# ADR 0004

## Title

Maintain AI Provider Independence

---

## Status

Accepted

---

## Context

AI providers evolve rapidly.

Depending on a single provider creates unnecessary risk.

---

## Decision

The AI layer will remain provider independent.

Supported providers may include:

- NVIDIA NIM
- OpenRouter
- Ollama
- OpenAI
- Future providers

---

## Reasons

- Flexibility
- Easier experimentation
- Reduced vendor lock-in
- Future proof architecture

---

## Consequences

The application will communicate with AI providers through an abstraction layer instead of directly coupling implementation to a single service.
