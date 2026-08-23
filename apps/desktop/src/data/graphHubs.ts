// Single source of truth for the knowledge-graph hub taxonomy, shared by
// GraphCanvas.tsx (renders the actual graph) and RightColumn.tsx (renders
// the filter legend + node/link counts). Previously each file hardcoded
// its own independent leaf list/count and the two silently drifted out of
// sync - importing from here instead of duplicating keeps that impossible.
//
// Only "conversations" is backed by live data (GraphCanvas fetches real
// conversation titles at render time); every other hub's leaves are
// static placeholder text.

export interface GraphHub {
  key: string;
  label: string;
  color: string;
  leaves: number;
}

export const HUB_LEAVES: Record<string, string[]> = {
  skills: ["Python", "React", "TypeScript", "Rust", "FastAPI", "Tauri"],
  tools: ["Web Search", "Memory", "File System", "Terminal", "Browser", "Calculator"],
  files: ["Documents", "Downloads", "Projects", "Desktop", "Pictures", "Music"],
  notes: ["JARVIS Notes", "Ideas", "Tasks", "Meeting Notes", "Code Snippets"],
  // Current model defaults per provider (services/jarvis-engine .env / core/config.py):
  // Gemini, Groq, Ollama respectively. Keep in sync if those defaults change.
  models: ["gemini-3.6-flash", "openai/gpt-oss-20b", "phi4-mini"],
  worlds: ["Home", "Work", "Projects", "Archive"],
  conversations: [],
};

const HUB_META: Array<{ key: keyof typeof HUB_LEAVES; label: string; color: string }> = [
  { key: "skills", label: "Skills", color: "#5aa9e6" },
  { key: "tools", label: "Tools", color: "#e85aa0" },
  { key: "files", label: "Files", color: "#7a8c93" },
  { key: "notes", label: "Notes", color: "#52d68a" },
  { key: "worlds", label: "Worlds", color: "#e8934b" },
  { key: "models", label: "Models", color: "#b98be8" },
  { key: "conversations", label: "Conversations", color: "#ffb454" },
];

export const GRAPH_HUBS: GraphHub[] = HUB_META.map((h) => ({
  ...h,
  leaves: HUB_LEAVES[h.key].length,
}));
