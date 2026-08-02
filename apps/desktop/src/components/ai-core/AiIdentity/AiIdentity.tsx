import { cn } from "../../../lib/cn";

export interface AiIdentityProps {
  className?: string;
}

export function AiIdentity({ className }: AiIdentityProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center text-center", className)}>
      <h1 className="font-mono text-[var(--font-size-section)] font-semibold tracking-wider text-[var(--color-text-primary)]">
        JARVIS
      </h1>
      <p className="text-[var(--font-size-sm)] text-[var(--color-text-muted)]">
        Personal AI Assistant
      </p>
    </div>
  );
}
