import { cn } from "../../../lib/cn";
import { AiCore } from "../AiCore/AiCore";
import { AiIdentity } from "../AiIdentity/AiIdentity";
import { SuggestionGrid } from "../SuggestionGrid/SuggestionGrid";
import { WelcomeMessage } from "../WelcomeMessage/WelcomeMessage";

export interface IdleViewProps {
  className?: string;
}

export function IdleView({ className }: IdleViewProps) {
  return (
    <div
      className={cn(
        "flex min-h-full w-full flex-col items-center justify-center gap-[var(--space-12)] p-[var(--space-8)]",
        className,
      )}
    >
      <div className="flex flex-col items-center gap-[var(--space-6)]">
        <AiCore />
        <AiIdentity />
      </div>

      <WelcomeMessage />

      <SuggestionGrid />
    </div>
  );
}
