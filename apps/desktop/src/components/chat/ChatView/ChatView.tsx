import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import type { Easing } from "framer-motion";
import { cn } from "../../../lib/cn";
import { IdleView } from "../../ai-core/IdleView/IdleView";
import { ConversationArea } from "../ConversationArea/ConversationArea";
import { ChatComposer } from "../ChatComposer/ChatComposer";
import { useJarvisChat } from "../../../hooks/useJarvisChat";
import { useConversationStore } from "../../../stores/useConversationStore";
import { SquarePen } from "lucide-react";
import { IconButton } from "../../ui/IconButton/IconButton";

export interface ChatViewProps {
  className?: string;
}

export function ChatView({ className }: ChatViewProps) {
  const { messages, sendUserMessage, isTyping } = useJarvisChat();
  const clearConversation = useConversationStore((state) => state.clearConversation);

  const hasMessages = messages.length > 0;
  const shouldReduceMotion = useReducedMotion();
  const transition = { duration: shouldReduceMotion ? 0 : 0.25, ease: "easeOut" as Easing };

  return (
    <div className={cn("flex h-full w-full flex-col", className)}>
      <div className="flex-1 min-h-0 overflow-hidden relative">
        {hasMessages && (
          <div className="absolute top-[var(--space-4)] right-[var(--space-4)] z-10">
            <IconButton 
              aria-label="New conversation" 
              onClick={clearConversation}
            >
              <SquarePen />
            </IconButton>
          </div>
        )}
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
        <ChatComposer onSend={sendUserMessage} />
      </div>
    </div>
  );
}
