/* eslint-disable no-unused-vars */
import { create } from "zustand";

export interface AIState {
  provider: "ollama" | "openrouter" | "groq" | "gemini";
  model: string;
  status: "idle" | "connecting" | "streaming" | "error" | "offline";
  voiceStatus: "idle" | "listening" | "processing" | "speaking";
  isStreaming: boolean;
  error: string | null;
  memoryCount: number;
  openrouterKey: string;
  groqKey: string;
  geminiKey: string;
  setProvider: (provider: AIState["provider"]) => void;
  setModel: (model: string) => void;
  setStatus: (status: AIState["status"]) => void;
  setVoiceStatus: (status: AIState["voiceStatus"]) => void;
  setStreaming: (value: boolean) => void;
  setError: (error: string | null) => void;
  setMemoryCount: (count: number) => void;
  setOpenrouterKey: (key: string) => void;
  setGroqKey: (key: string) => void;
  setGeminiKey: (key: string) => void;
}

export const useAIStore = create<AIState>((set) => ({
  provider: "ollama",
  model: "llama3.2:3b",
  status: "idle",
  voiceStatus: "idle",
  isStreaming: false,
  error: null,
  memoryCount: 0,
  openrouterKey: "",
  groqKey: "",
  geminiKey: "",
  setProvider: (provider) => set({ provider }),
  setModel: (model) => set({ model }),
  setStatus: (status) => set({ status }),
  setVoiceStatus: (status) => set({ voiceStatus: status }),
  setStreaming: (value) => set({ isStreaming: value }),
  setError: (error) => set({ error }),
  setMemoryCount: (count) => set({ memoryCount: count }),
  setOpenrouterKey: (key) => set({ openrouterKey: key }),
  setGroqKey: (key) => set({ groqKey: key }),
  setGeminiKey: (key) => set({ geminiKey: key }),
}));
