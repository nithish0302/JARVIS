/* eslint-disable no-unused-vars */
import { create } from "zustand";

export interface AppState {
  view: "chat" | "settings";
  setView: (view: "chat" | "settings") => void;
}

export const useAppStore = create<AppState>((set) => ({
  view: "chat",
  setView: (view) => set({ view }),
}));
