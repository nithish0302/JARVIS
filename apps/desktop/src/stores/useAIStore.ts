import { create } from "zustand";

export interface AIState {
  provider: "ollama" | "openrouter" | "claude";
  model: string;
  status: "idle" | "connecting" | "streaming" | "error" | "offline";
  isStreaming: boolean;
  error: string | null;
  setProvider: (provider: AIState["provider"]) => void;
  setModel: (model: string) => void;
  setStatus: (status: AIState["status"]) => void;
  setStreaming: (value: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAIStore = create<AIState>((set) => ({
  provider: "ollama",
  model: "llama3.2:3b",
  status: "idle",
  isStreaming: false,
  error: null,
  setProvider: (provider) => set({ provider }),
  setModel: (model) => set({ model }),
  setStatus: (status) => set({ status }),
  setStreaming: (value) => set({ isStreaming: value }),
  setError: (error) => set({ error }),
}));
