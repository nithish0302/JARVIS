import { cn } from "../../../lib/cn";
import { AiCoreIdle } from "../AiCoreIdle/AiCoreIdle";

export interface AiCoreProps {
  className?: string;
  state?: "idle";
}

export function AiCore({ className, state = "idle" }: AiCoreProps) {
  return (
    <div
      aria-hidden="true"
      className={cn("relative size-[var(--space-16)] shrink-0", className)}
    >
      {state === "idle" ? <AiCoreIdle /> : null}
    </div>
  );
}
