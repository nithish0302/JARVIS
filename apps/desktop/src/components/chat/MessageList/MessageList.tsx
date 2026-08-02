import type { Message } from "../../../types/chat.types";
import { cn } from "../../../lib/cn";
import { MessageBubble } from "../MessageBubble/MessageBubble";

export interface MessageListProps {
  className?: string;
  messages: Message[];
}

export function MessageList({ className, messages }: MessageListProps) {
  if (messages.length === 0) {
    return null;
  }

  return (
    <div
      aria-live="polite"
      className={cn("flex w-full flex-col gap-[var(--space-6)]", className)}
      role="log"
    >
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          content={message.content}
          role={message.role}
          timestamp={message.timestamp}
        />
      ))}
    </div>
  );
}
