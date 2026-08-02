import { useState } from "react";
import type { Message } from "../../../types/chat.types";
import { cn } from "../../../lib/cn";
import { IdleView } from "../../ai-core/IdleView/IdleView";
import { ConversationArea } from "../ConversationArea/ConversationArea";
import { ChatComposer } from "../ChatComposer/ChatComposer";

export interface ChatViewProps {
  className?: string;
}

// Temporary static data for Milestone 3 presentation validation, now used as initial state
const INITIAL_MOCK_MESSAGES: Message[] = [
  {
    id: "1",
    role: "user",
    content: "Initialize system diagnostics.",
    timestamp: "10:00 AM",
  },
  {
    id: "2",
    role: "assistant",
    content: "System diagnostics initialized. All core parameters are operating within normal ranges. Memory modules are online and available. What would you like to investigate first?",
    timestamp: "10:00 AM",
  },
  {
    id: "3",
    role: "user",
    content: "Check the visual interface latency.",
    timestamp: "10:01 AM",
  },
];

export function ChatView({ className }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MOCK_MESSAGES);
  const hasMessages = messages.length > 0;

  const handleSend = (text: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  return (
    <div className={cn("flex h-full w-full flex-col", className)}>
      <div className="flex-1 min-h-0 overflow-hidden relative">
        {hasMessages ? (
          <ConversationArea isTyping={false} messages={messages} />
        ) : (
          <IdleView />
        )}
      </div>
      <div className="shrink-0 p-[var(--space-4)] pt-0">
        <ChatComposer onSend={handleSend} />
      </div>
    </div>
  );
}
