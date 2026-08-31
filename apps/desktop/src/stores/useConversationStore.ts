import { create } from "zustand";
import type { Message } from "../types/chat.types";

export interface ConversationState {
  messages: Message[];
  currentConversationId: string | null;
  isTyping: boolean;
  streamingMessageId: string | null;
  streamingContent: string;
  streamingSearchQuery: string | null;
  currentConversationTitle: string | null;
  isStreaming: boolean;
  isSearching: boolean;
  searchingQuery: string;
  addMessage: (message: Message) => void;
  setTyping: (value: boolean) => void;
  setConversationId: (id: string) => void;
  setConversationTitle: (title: string | null) => void;
  clearConversation: () => void;
  startStreaming: (messageId: string) => void;
  appendStreamToken: (token: string) => void;
  finishStreaming: () => void;
  setStreamingMeta: (query: string | null) => void;
  setMessages: (messages: Message[]) => void;
  setSearching: (searching: boolean, query?: string) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  messages: [],
  currentConversationId: null,
  isTyping: false,
  streamingMessageId: null,
  streamingContent: "",
  streamingSearchQuery: null,
  currentConversationTitle: null,
  isStreaming: false,
  isSearching: false,
  searchingQuery: "",
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setTyping: (value) => set({ isTyping: value }),
  setConversationId: (id) => {
    window.localStorage?.setItem("jarvis_conversation_id", id);
    set({ currentConversationId: id });
  },
  setConversationTitle: (title) => set({ currentConversationTitle: title }),
  clearConversation: () => {
    window.localStorage?.removeItem("jarvis_conversation_id");
    set({ 
      messages: [], 
      currentConversationId: null,
      currentConversationTitle: null,
      isTyping: false, 
      streamingMessageId: null, 
      streamingContent: "",
      streamingSearchQuery: null,
      isStreaming: false,
      isSearching: false,
      searchingQuery: ""
    });
  },
  startStreaming: (messageId) => set({ streamingMessageId: messageId, streamingContent: "", streamingSearchQuery: null, isStreaming: true }),
  appendStreamToken: (token) => set((state) => ({ 
    streamingContent: (state.streamingContent + token).replace(/\[UI_ACTION:[^\]]*\]/g, "")
  })),
  finishStreaming: () => set({ streamingMessageId: null, streamingContent: "", streamingSearchQuery: null, isStreaming: false, isSearching: false }),
  setStreamingMeta: (query) => set({ streamingSearchQuery: query }),
  setMessages: (messages) => set({ messages }),
  setSearching: (searching, query) => set({ isSearching: searching, ...(query !== undefined && { searchingQuery: query }) }),
}));
