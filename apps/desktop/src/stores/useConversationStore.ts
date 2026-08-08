import { create } from "zustand";
import type { Message } from "../types/chat.types";

export interface ConversationState {
  messages: Message[];
  currentConversationId: string | null;
  isTyping: boolean;
  addMessage: (message: Message) => void;
  setTyping: (value: boolean) => void;
  clearConversation: () => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  messages: [],
  currentConversationId: null,
  isTyping: false,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setTyping: (value) => set({ isTyping: value }),
  clearConversation: () => set({ messages: [], currentConversationId: null, isTyping: false }),
}));
