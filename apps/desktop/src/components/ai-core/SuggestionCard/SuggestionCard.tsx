import { cn } from "../../../lib/cn";
import { Card } from "../../ui/Card/Card";

export interface SuggestionCardProps {
  className?: string;
  label: string;
}

export function SuggestionCard({ className, label }: SuggestionCardProps) {
  return (
    <Card
      className={cn(
        "flex min-h-[var(--space-16)] items-center justify-center p-[var(--space-4)] text-center text-[var(--font-size-sm)] text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-border-hover)]",
        className,
      )}
    >
      {label}
    </Card>
  );
}
