import { cn } from "../../../lib/cn";
import { Card } from "../../ui/Card/Card";
import { MessageAvatar } from "../MessageAvatar/MessageAvatar";

export interface MessageBubbleProps {
  className?: string;
  content: string;
  role: "user" | "assistant";
  timestamp: string;
}

export function MessageBubble({ className, content, role, timestamp }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-[var(--space-4)]",
        isUser ? "flex-row-reverse" : "flex-row",
        className,
      )}
    >
      <MessageAvatar role={role} />
      <div
        className={cn(
          "flex flex-col gap-[var(--space-1)]",
          isUser ? "items-end" : "items-start",
        )}
      >
        <div className="flex items-center gap-[var(--space-2)] text-[var(--font-size-caption)] text-[var(--color-text-muted)]">
          <span className="font-medium">{isUser ? "You" : "JARVIS"}</span>
          <span>&bull;</span>
          <span>{timestamp}</span>
        </div>
        <Card
          className={cn(
            "p-[var(--space-3)] text-[var(--font-size-body)]",
            isUser
              ? "bg-[var(--color-accent)] text-[var(--color-background)]"
              : "bg-[var(--color-surface)] text-[var(--color-text-primary)]",
          )}
        >
          {content}
        </Card>
      </div>
    </div>
  );
}
