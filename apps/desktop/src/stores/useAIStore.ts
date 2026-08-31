import { create } from "zustand";

export interface AIState {
  provider: "ollama" | "openrouter" | "groq" | "gemini";
  model: string;
  status: "idle" | "connecting" | "streaming" | "error" | "offline";
  // "continuous" = continuous conversation mode is active and JARVIS is
  // listening for a follow-up command directly, with no wake word needed
  // (see services/jarvis-engine voice_manager.py's continue_conversation()).
  voiceStatus: "idle" | "listening" | "processing" | "speaking" | "continuous";
  isStreaming: boolean;
  error: string | null;
  memoryCount: number;
  openrouterKey: string;
  groqKey: string;
  geminiKey: string;
  personalityMode: "assistant" | "developer" | "research";
  modifier: "none" | "planner" | "quiet";
  addressPreference: string;
  dailyBriefingEnabled: boolean;
  // provider_override: locks the cascade to a single provider (null = normal
  // Gemini -> OpenRouter -> Groq -> Ollama fallback). fallbackMode "ask"
  // pauses on a failure and asks which provider to use next instead of
  // auto-advancing.
  providerOverride: AIState["provider"] | null;
  fallbackMode: "auto" | "ask";
  // Set from the LAST ACTUAL response (chat or voice) so the Topbar badge
  // is honest about what really answered, not a static config value.
  lastFallbackOccurred: boolean;
  lastFailedProvider: string | null;
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
  setPersonalityMode: (mode: AIState["personalityMode"]) => void;
  setModifier: (modifier: AIState["modifier"]) => void;
  setAddressPreference: (value: string) => void;
  setDailyBriefingEnabled: (value: boolean) => void;
  setProviderOverride: (value: AIState["provider"] | null) => void;
  setFallbackMode: (value: "auto" | "ask") => void;
  setLastFallback: (occurred: boolean, failedProvider: string | null) => void;
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
  personalityMode: "assistant",
  modifier: "none",
  addressPreference: "sir",
  dailyBriefingEnabled: true,
  providerOverride: null,
  fallbackMode: "auto",
  lastFallbackOccurred: false,
  lastFailedProvider: null,
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
  setPersonalityMode: (personalityMode) => set({ personalityMode }),
  setModifier: (modifier) => set({ modifier }),
  setAddressPreference: (addressPreference) => set({ addressPreference }),
  setDailyBriefingEnabled: (dailyBriefingEnabled) => set({ dailyBriefingEnabled }),
  setProviderOverride: (providerOverride) => set({ providerOverride }),
  setFallbackMode: (fallbackMode) => set({ fallbackMode }),
  setLastFallback: (occurred, failedProvider) => set({
    lastFallbackOccurred: occurred,
    lastFailedProvider: failedProvider,
  }),
}));
