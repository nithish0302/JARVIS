import { cn } from "../../../lib/cn";
import { SuggestionCard } from "../SuggestionCard/SuggestionCard";

export interface SuggestionGridProps {
  className?: string;
}

export function SuggestionGrid({ className }: SuggestionGridProps) {
  return (
    <div className={cn("grid w-full max-w-2xl grid-cols-2 gap-[var(--space-4)]", className)}>
      <SuggestionCard label="Ask a question" />
      <SuggestionCard label="Write some code" />
      <SuggestionCard label="Summarize a document" />
      <SuggestionCard label="Analyze data" />
    </div>
  );
}
