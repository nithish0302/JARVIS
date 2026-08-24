// Single source of truth for the knowledge-graph hub taxonomy, shared by
// GraphCanvas.tsx (renders the actual graph) and RightColumn.tsx (renders
// the filter legend + node/link counts). Previously each file hardcoded
// its own independent leaf list/count and the two silently drifted out of
// sync - importing from here instead of duplicating keeps that impossible.
//
// "conversations" and "memories" are backed by live data (GraphCanvas
// fetches real conversation titles / memory records at render time);
// every other hub's leaves are static placeholder text.

import { CURRENT_MODEL_DEFAULTS } from "./currentModels";

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
  models: [
    CURRENT_MODEL_DEFAULTS.gemini,
    CURRENT_MODEL_DEFAULTS.groq,
    CURRENT_MODEL_DEFAULTS.ollama,
  ],
  worlds: ["Home", "Work", "Projects", "Archive"],
  conversations: [],
  memories: [],
};

// Per-category colors for memory leaves - distinct from the memories hub's
// own color so category sub-clusters read as visually separate groups
// (mirrors how the conversations hub tints its own leaves by role).
export const MEMORY_CATEGORY_COLORS: Record<string, string> = {
  personal: "#52d68a",
  preference: "#5aa9e6",
  project: "#e8934b",
  goal: "#e85aa0",
  fact: "#b98be8",
  general: "#7a8c93",
};

export const MEMORY_CATEGORIES = ["personal", "preference", "project", "goal", "fact"];

const HUB_META: Array<{ key: keyof typeof HUB_LEAVES; label: string; color: string }> = [
  { key: "skills", label: "Skills", color: "#5aa9e6" },
  { key: "tools", label: "Tools", color: "#e85aa0" },
  { key: "files", label: "Files", color: "#7a8c93" },
  { key: "notes", label: "Notes", color: "#52d68a" },
  { key: "worlds", label: "Worlds", color: "#e8934b" },
  { key: "models", label: "Models", color: "#b98be8" },
  { key: "conversations", label: "Conversations", color: "#ffb454" },
  { key: "memories", label: "Memories", color: "#4fd1c5" },
];

export const GRAPH_HUBS: GraphHub[] = HUB_META.map((h) => ({
  ...h,
  leaves: HUB_LEAVES[h.key].length,
}));
