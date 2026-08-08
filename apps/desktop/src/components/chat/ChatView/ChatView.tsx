import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import type { Easing } from "framer-motion";
import type { Message } from "../../../types/chat.types";
import { cn } from "../../../lib/cn";
import { IdleView } from "../../ai-core/IdleView/IdleView";
import { ConversationArea } from "../ConversationArea/ConversationArea";
import { ChatComposer } from "../ChatComposer/ChatComposer";

import { useConversationStore } from "../../../stores/useConversationStore";

export interface ChatViewProps {
  className?: string;
}

export function ChatView({ className }: ChatViewProps) {
  const messages = useConversationStore((state) => state.messages);
  const isTyping = useConversationStore((state) => state.isTyping);
  const addMessage = useConversationStore((state) => state.addMessage);

  const hasMessages = messages.length > 0;
  const shouldReduceMotion = useReducedMotion();
  const transition = { duration: shouldReduceMotion ? 0 : 0.25, ease: "easeOut" as Easing };

  const handleSend = (text: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    addMessage(newMessage);
  };

  return (
    <div className={cn("flex h-full w-full flex-col", className)}>
      <div className="flex-1 min-h-0 overflow-hidden relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={hasMessages ? "chat" : "idle"}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex flex-col"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            transition={transition}
          >
            {hasMessages ? <ConversationArea isTyping={isTyping} messages={messages} /> : <IdleView />}
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="shrink-0 border-t border-solid border-t-[var(--color-border-subtle)] [border-width:var(--border-width)] p-[var(--space-4)]">
        <ChatComposer onSend={handleSend} />
      </div>
    </div>
  );
}
