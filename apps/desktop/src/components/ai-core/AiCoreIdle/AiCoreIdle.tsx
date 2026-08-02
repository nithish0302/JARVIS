import { motion, useReducedMotion } from "framer-motion";
import { cn } from "../../../lib/cn";

export interface AiCoreIdleProps {
  className?: string;
}

export function AiCoreIdle({ className }: AiCoreIdleProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div className={cn("relative flex h-full w-full items-center justify-center", className)}>
      <motion.div
        animate={
          prefersReducedMotion
            ? { opacity: 0.8 }
            : {
                scale: [1, 1.05, 1],
                opacity: [0.6, 0.9, 0.6],
              }
        }
        className="absolute h-full w-full rounded-[var(--radius-full)] bg-[var(--color-highlight)] [filter:var(--glow-md)]"
        transition={{
          duration: 4,
          ease: "easeInOut",
          repeat: Infinity,
        }}
      />
      <div className="absolute h-[80%] w-[80%] rounded-[var(--radius-full)] bg-[var(--color-highlight)] opacity-80" />
    </div>
  );
}
