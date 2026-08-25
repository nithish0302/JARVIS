import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "../../../stores/useAppStore";

/**
 * Visual indicator shown whenever a chat/voice response actually fell back
 * to a different AI provider than the one first tried. Rendered at App
 * level (top-right) so it's distinct from ShortcutToast (bottom-center).
 */
export function FallbackToast() {
  const message = useAppStore((s) => s.fallbackToast);
  const visible = useAppStore((s) => s.fallbackToastVisible);

  return (
    <AnimatePresence>
      {visible && message && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
          className="pointer-events-none fixed right-6 top-16 z-[10001] max-w-[360px] rounded-[10px] border border-[var(--color-amber,#f59e0b)] bg-[rgba(20,14,4,0.92)] px-4 py-2 font-mono text-[11px] tracking-[0.5px] text-[var(--color-amber,#f59e0b)] shadow-[0_0_24px_rgba(245,158,11,0.2)] backdrop-blur-md"
        >
          ⚠ {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
