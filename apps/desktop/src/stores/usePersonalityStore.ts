import { create } from "zustand";

export interface PersonalityState {
  mode: "assistant" | "developer" | "focus" | "executive" | "learning" | "automation";
  address: "sir" | "Nithish" | "boss";
  formality: number;
  verbosity: number;
  humor: number;
  proactivity: number;
  setMode: (mode: PersonalityState["mode"]) => void;
  setAddress: (address: PersonalityState["address"]) => void;
  setDial: (key: "formality" | "verbosity" | "humor" | "proactivity", value: number) => void;
}

export const usePersonalityStore = create<PersonalityState>((set) => ({
  mode: "assistant",
  address: "sir",
  formality: 60,
  verbosity: 50,
  humor: 40,
  proactivity: 50,
  setMode: (mode) => set({ mode }),
  setAddress: (address) => set({ address }),
  setDial: (key, value) => set((state) => ({ ...state, [key]: value })),
}));
