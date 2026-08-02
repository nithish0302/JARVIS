import { useEffect, useRef } from "react";
import type { ElementRef } from "react";
import type { Message } from "../../../types/chat.types";
import { cn } from "../../../lib/cn";
import { MessageList } from "../MessageList/MessageList";
import { TypingIndicator } from "../TypingIndicator/TypingIndicator";

export interface ConversationAreaProps {
  className?: string;
  isTyping?: boolean;
  messages: Message[];
}

export function ConversationArea({ className, isTyping = false, messages }: ConversationAreaProps) {
  const bottomRef = useRef<ElementRef<"div">>(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  return (
    <div
      className={cn(
        "flex w-full flex-col px-[var(--space-6)] py-[var(--space-8)]",
        className,
      )}
    >
      <MessageList messages={messages} />
      
      {isTyping && (
        <div className="mt-[var(--space-6)] self-start">
          <TypingIndicator visible={true} />
        </div>
      )}
      
      {/* Scroll anchor */}
      <div ref={bottomRef} className="h-px w-full shrink-0" />
    </div>
  );
}
