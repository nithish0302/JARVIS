import { cn } from "../../../lib/cn";

export interface MessageAvatarProps {
  className?: string;
  role: "user" | "assistant";
}

export function MessageAvatar({ className, role }: MessageAvatarProps) {
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-[var(--radius-full)] size-[var(--space-8)]",
        role === "user" ? "bg-[var(--color-surface)]" : "bg-transparent",
        className,
      )}
    >
      {role === "user" ? (
        <span className="text-[var(--font-size-sm)] font-medium text-[var(--color-text-secondary)]">
          U
        </span>
      ) : (
        <div className="relative flex h-full w-full items-center justify-center">
          <div className="absolute h-full w-full rounded-[var(--radius-full)] bg-[var(--color-highlight)] [filter:var(--glow-sm)] opacity-60" />
          <div className="absolute h-3/4 w-3/4 rounded-[var(--radius-full)] bg-[var(--color-highlight)] opacity-90" />
        </div>
      )}
    </div>
  );
}
