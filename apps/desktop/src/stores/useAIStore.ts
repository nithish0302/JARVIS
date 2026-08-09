/* eslint-disable no-unused-vars */
import { create } from "zustand";

export interface AIState {
  provider: "ollama" | "openrouter" | "claude";
  model: string;
  status: "idle" | "connecting" | "streaming" | "error" | "offline";
  isStreaming: boolean;
  error: string | null;
  memoryCount: number;
  openrouterKey: string;
  setProvider: (provider: AIState["provider"]) => void;
  setModel: (model: string) => void;
  setStatus: (status: AIState["status"]) => void;
  setStreaming: (value: boolean) => void;
  setError: (error: string | null) => void;
  setMemoryCount: (count: number) => void;
  setOpenrouterKey: (key: string) => void;
}

export const useAIStore = create<AIState>((set) => ({
  provider: "ollama",
  model: "llama3.2:3b",
  status: "idle",
  isStreaming: false,
  error: null,
  memoryCount: 0,
  openrouterKey: "",
  setProvider: (provider) => set({ provider }),
  setModel: (model) => set({ model }),
  setStatus: (status) => set({ status }),
  setStreaming: (value) => set({ isStreaming: value }),
  setError: (error) => set({ error }),
  setMemoryCount: (count) => set({ memoryCount: count }),
  setOpenrouterKey: (key) => set({ openrouterKey: key }),
}));
