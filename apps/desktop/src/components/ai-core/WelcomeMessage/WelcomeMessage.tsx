import { cn } from "../../../lib/cn";

export interface WelcomeMessageProps {
  className?: string;
}

export function WelcomeMessage({ className }: WelcomeMessageProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center text-center gap-[var(--space-2)]", className)}>
      <h2 className="text-[var(--font-size-page)] font-semibold text-[var(--color-text-primary)]">
        Hello.
      </h2>
      <p className="text-[var(--font-size-body)] text-[var(--color-text-secondary)]">
        How can I help you today?
      </p>
    </div>
  );
}
