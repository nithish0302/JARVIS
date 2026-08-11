/* eslint-disable no-unused-vars */
import { create } from "zustand";

export interface AppState {
  view: "chat" | "settings";
  setView: (view: "chat" | "settings") => void;
  graphOpen: boolean;
  graphFocused: boolean;
  activeHub: string | null;
  conversationPanelOpen: boolean;
  chatMode: boolean;
  setGraphOpen: (open: boolean) => void;
  setGraphFocused: (focused: boolean) => void;
  setActiveHub: (hub: string | null) => void;
  setConversationPanelOpen: (open: boolean) => void;
  setChatMode: (enabled: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  view: "chat",
  setView: (view) => set({ view }),
  graphOpen: true,
  graphFocused: true,
  activeHub: null,
  conversationPanelOpen: false,
  chatMode: false,
  setGraphOpen: (open) => set({ graphOpen: open }),
  setGraphFocused: (focused) => set({ graphFocused: focused }),
  setActiveHub: (hub) => set({ activeHub: hub }),
  setConversationPanelOpen: (open) => set({ conversationPanelOpen: open }),
  setChatMode: (enabled) => set({ chatMode: enabled }),
}));
