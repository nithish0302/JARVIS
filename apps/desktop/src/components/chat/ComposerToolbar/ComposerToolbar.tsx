import { cn } from "../../../lib/cn";

export interface ComposerToolbarProps {
  className?: string;
}

export function ComposerToolbar({ className }: ComposerToolbarProps) {
  return (
    <div
      className={cn(
        "flex min-h-[var(--space-8)] w-full items-center gap-[var(--space-2)] px-[var(--space-2)] py-[var(--space-1)]",
        className,
      )}
    >
      {/* Future toolbar actions (e.g., attach file, voice input) will go here */}
    </div>
  );
}
