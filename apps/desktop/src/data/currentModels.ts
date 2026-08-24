// Single source of truth for each provider's CURRENT default model, mirrored
// from services/jarvis-engine/src/jarvis_engine/core/config.py (OLLAMA_MODEL,
// GROQ_MODEL, GEMINI_MODEL). The backend is Python and the frontend is
// TypeScript, so this can't be a live import - it's a deliberate, single
// hand-maintained mirror. graphHubs.ts and AIProviderSection both read from
// here instead of each keeping their own copy, so the two can't drift apart
// from each other the way they previously drifted from the backend.
//
// Keep this in sync if those config.py defaults change.
export const CURRENT_MODEL_DEFAULTS = {
  gemini: "gemini-3.6-flash",
  groq: "openai/gpt-oss-20b",
  ollama: "phi4-mini",
} as const;

export type ModelDefaultProvider = keyof typeof CURRENT_MODEL_DEFAULTS;
