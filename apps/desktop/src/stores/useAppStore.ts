/* eslint-disable no-unused-vars */
import { create } from "zustand";

export interface AppState {
  view: "chat" | "settings" | "gaps" | "capabilities";
  setView: (view: "chat" | "settings" | "gaps" | "capabilities") => void;
  unresolvedGapCount: number;
  setUnresolvedGapCount: (count: number) => void;
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
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  // Incrementing token rather than a boolean flag: ConversationPanel
  // watches it in an effect and focuses its search input on every change,
  // so pressing Ctrl+F repeatedly re-focuses instead of latching once.
  conversationSearchFocusToken: number;
  requestConversationSearchFocus: () => void;
  // Separate from actionFeedback (which only renders inside the Orb, and
  // so is invisible in settings view) - this one renders at App level so
  // shortcut confirmations show up from anywhere.
  shortcutToast: string;
  shortcutToastVisible: boolean;
  showShortcutToast: (message: string) => void;
  // Full memory record for the leaf last clicked in the memories hub - the
  // Inspector panel reads this to show/edit it. Cleared whenever a
  // different hub or leaf is selected.
  selectedMemory: Record<string, any> | null;
  setSelectedMemory: (memory: Record<string, any> | null) => void;
  deletingMemoryId: string | null;
  setDeletingMemoryId: (id: string | null) => void;
  // Bumped after an edit/delete so GraphCanvas's memory-fetch effect
  // re-runs and the hub's leaves reflect the change immediately.
  memoriesVersion: number;
  bumpMemoriesVersion: () => void;
  // Bumped whenever a voice turn creates or appends to a conversation,
  // so ConversationPanel's sidebar list can refetch without the panel
  // having to poll or the caller remembering to call refreshConversations()
  // itself - same pattern as memoriesVersion/bumpMemoriesVersion above.
  conversationsVersion: number;
  bumpConversationsVersion: () => void;
  // "Jump to node" (command palette -> graph). GraphCanvas watches this to
  // locate the leaf in the hub's full (real, backend-sourced) leaf list,
  // page its pagination to whichever page actually contains it, and pulse
  // the real rendered leaf there - independent of the activeHub-driven
  // hub-selection flow, since jumping to a different leaf within the hub
  // you're already viewing wouldn't otherwise re-trigger anything.
  focusLeaf: { hub: string; leafId: string } | null;
  setFocusLeaf: (focus: { hub: string; leafId: string } | null) => void;
  // Small visual indicator shown whenever a chat/voice response actually
  // fell back to a different AI provider than the one that was first
  // tried - separate from shortcutToast since it needs a longer, more
  // informative message and a distinct timeout.
  fallbackToast: string;
  fallbackToastVisible: boolean;
  showFallbackToast: (message: string) => void;
  // True once /settings confirms NO provider (Gemini/Groq/OpenRouter/
  // Ollama) has any key/host configured - the "fresh install, nothing set
  // up yet" state. Drives FirstRunBanner and the one-time auto-open of
  // Settings > Providers in useEngineStatus.
  providerUnconfigured: boolean;
  setProviderUnconfigured: (unconfigured: boolean) => void;
  // Which SettingsView section to land on when navigating to the settings
  // view - read once by SettingsView on mount, then cleared. Lets
  // useEngineStatus's first-run auto-open land directly on "providers"
  // instead of the default "ai-provider" section.
  settingsInitialSection: string | null;
  setSettingsInitialSection: (section: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  view: "chat",
  setView: (view) => set({ view }),
  unresolvedGapCount: 0,
  setUnresolvedGapCount: (count) => set({ unresolvedGapCount: count }),
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
  commandPaletteOpen: false,
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  conversationSearchFocusToken: 0,
  requestConversationSearchFocus: () =>
    set((state) => ({
      conversationSearchFocusToken: state.conversationSearchFocusToken + 1,
    })),
  shortcutToast: "",
  shortcutToastVisible: false,
  showShortcutToast: (message) => {
    if ((window as any)._shortcutToastTimer) {
      clearTimeout((window as any)._shortcutToastTimer);
    }
    set({ shortcutToast: message, shortcutToastVisible: true });
    (window as any)._shortcutToastTimer = setTimeout(() => {
      set({ shortcutToast: "", shortcutToastVisible: false });
      (window as any)._shortcutToastTimer = null;
    }, 2000);
  },
  selectedMemory: null,
  setSelectedMemory: (memory) => set({ selectedMemory: memory }),
  deletingMemoryId: null,
  setDeletingMemoryId: (id) => set({ deletingMemoryId: id }),
  memoriesVersion: 0,
  bumpMemoriesVersion: () => set((state) => ({ memoriesVersion: state.memoriesVersion + 1 })),
  conversationsVersion: 0,
  bumpConversationsVersion: () => set((state) => ({ conversationsVersion: state.conversationsVersion + 1 })),
  focusLeaf: null,
  setFocusLeaf: (focus) => set({ focusLeaf: focus }),
  fallbackToast: "",
  fallbackToastVisible: false,
  showFallbackToast: (message) => {
    if ((window as any)._fallbackToastTimer) {
      clearTimeout((window as any)._fallbackToastTimer);
    }
    set({ fallbackToast: message, fallbackToastVisible: true });
    (window as any)._fallbackToastTimer = setTimeout(() => {
      set({ fallbackToast: "", fallbackToastVisible: false });
      (window as any)._fallbackToastTimer = null;
    }, 5000);
  },
  providerUnconfigured: false,
  setProviderUnconfigured: (unconfigured) => set({ providerUnconfigured: unconfigured }),
  settingsInitialSection: null,
  setSettingsInitialSection: (section) => set({ settingsInitialSection: section }),
}));
