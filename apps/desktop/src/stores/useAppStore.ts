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
  graphLevel: 0 | 1 | 2;
  actionFeedback: string;
  actionFeedbackVisible: boolean;
  inspectorMessage: string;
  setGraphOpen: (open: boolean) => void;
  setGraphFocused: (focused: boolean) => void;
  setActiveHub: (hub: string | null) => void;
  setConversationPanelOpen: (open: boolean) => void;
  setChatMode: (enabled: boolean) => void;
  setGraphLevel: (level: 0 | 1 | 2) => void;
  showActionFeedback: (message: string) => void;
  clearActionFeedback: () => void;
  setInspectorMessage: (msg: string) => void;
  deletingConversationId: string | null;
  setDeletingConversationId: (id: string | null) => void;
  pendingCommand: string | null;
  setPendingCommand: (cmd: string | null) => void;
  graphMode: "2d" | "3d";
  isCharging: boolean;
  setGraphMode: (mode: "2d" | "3d") => void;
  setIsCharging: (charging: boolean) => void;
  voiceActive: boolean;
  setVoiceActive: (active: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  view: "chat",
  setView: (view) => set({ view }),
  graphOpen: true,
  graphFocused: true,
  activeHub: null,
  conversationPanelOpen: false,
  chatMode: false,
  graphLevel: 1,
  actionFeedback: "",
  actionFeedbackVisible: false,
  inspectorMessage: "",
  setGraphOpen: (open) => set({ graphOpen: open }),
  setGraphFocused: (focused) => set({ graphFocused: focused }),
  setActiveHub: (hub) => set({ activeHub: hub }),
  setConversationPanelOpen: (open) => set({ conversationPanelOpen: open }),
  setChatMode: (enabled) => set({ chatMode: enabled }),
  setGraphLevel: (level) => set({ graphLevel: level }),
  showActionFeedback: (message) => {
    if ((window as any)._feedbackTimer) {
      clearTimeout((window as any)._feedbackTimer);
    }
    set({ actionFeedback: message, actionFeedbackVisible: true });
    (window as any)._feedbackTimer = setTimeout(() => {
      set({ actionFeedback: "", actionFeedbackVisible: false });
      (window as any)._feedbackTimer = null;
    }, 5000);
  },
  clearActionFeedback: () => set({ actionFeedback: "", actionFeedbackVisible: false }),
  setInspectorMessage: (msg) => {
    set({ inspectorMessage: msg });
    setTimeout(() => {
      set((state) => (state.inspectorMessage === msg ? { inspectorMessage: "" } : state));
    }, 3000);
  },
  deletingConversationId: null,
  setDeletingConversationId: (id) => set({ deletingConversationId: id }),
  pendingCommand: null,
  setPendingCommand: (cmd) => set({ pendingCommand: cmd }),
  graphMode: "3d",
  isCharging: true,
  setGraphMode: (mode) => set({ graphMode: mode }),
  setIsCharging: (charging) => set({ isCharging: charging }),
  voiceActive: false,
  setVoiceActive: (active) => set({ voiceActive: active }),
}));
