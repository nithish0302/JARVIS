import { motion, useReducedMotion } from "framer-motion";
import { cn } from "../../../lib/cn";

export interface TypingIndicatorProps {
  className?: string;
  visible?: boolean;
}

export function TypingIndicator({ className, visible = false }: TypingIndicatorProps) {
  const prefersReducedMotion = useReducedMotion();

  if (!visible) return null;

  const dotVariants = {
    animate: {
      opacity: prefersReducedMotion ? [0.5, 1, 0.5] : 1,
      y: prefersReducedMotion ? 0 : [0, -4, 0],
    },
  };

  return (
    <div
      aria-label="Assistant is typing"
      className={cn("flex items-center gap-[var(--space-1)] p-[var(--space-2)]", className)}
      role="status"
    >
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate="animate"
          className="size-[var(--space-2)] rounded-[var(--radius-full)] bg-[var(--color-accent)]"
          initial={prefersReducedMotion ? { opacity: 0.5 } : { y: 0 }}
          transition={{
            delay: i * 0.15,
            duration: 0.6,
            ease: "easeInOut",
            repeat: Infinity,
          }}
          variants={dotVariants}
        />
      ))}
    </div>
  );
}
