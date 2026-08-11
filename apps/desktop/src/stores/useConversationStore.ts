/* eslint-disable no-unused-vars */
import { create } from "zustand";
import type { Message } from "../types/chat.types";

export interface ConversationState {
  messages: Message[];
  currentConversationId: string | null;
  isTyping: boolean;
  streamingMessageId: string | null;
  streamingContent: string;
  streamingSearchQuery: string | null;
  addMessage: (message: Message) => void;
  setTyping: (value: boolean) => void;
  setConversationId: (id: string) => void;
  clearConversation: () => void;
  startStreaming: (messageId: string) => void;
  appendStreamToken: (token: string) => void;
  finishStreaming: () => void;
  setStreamingMeta: (query: string | null) => void;
  setMessages: (messages: Message[]) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  messages: [],
  currentConversationId: null,
  isTyping: false,
  streamingMessageId: null,
  streamingContent: "",
  streamingSearchQuery: null,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setTyping: (value) => set({ isTyping: value }),
  setConversationId: (id) => {
    window.localStorage?.setItem("jarvis_conversation_id", id);
    set({ currentConversationId: id });
  },
  clearConversation: () => {
    window.localStorage?.removeItem("jarvis_conversation_id");
    set({ 
      messages: [], 
      currentConversationId: null, 
      isTyping: false, 
      streamingMessageId: null, 
      streamingContent: "",
      streamingSearchQuery: null 
    });
  },
  startStreaming: (messageId) => set({ streamingMessageId: messageId, streamingContent: "", streamingSearchQuery: null }),
  appendStreamToken: (token) => set((state) => ({ streamingContent: state.streamingContent + token })),
  finishStreaming: () => set({ streamingMessageId: null, streamingContent: "", streamingSearchQuery: null }),
  setStreamingMeta: (query) => set({ streamingSearchQuery: query }),
  setMessages: (messages) => set({ messages }),
}));
