import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "../../../stores/useAppStore";

/**
 * Small global confirmation for keyboard shortcuts. Rendered at App level
 * (unlike ActionFeedback, which lives inside the Orb and is therefore
 * invisible in settings view) so shortcut feedback shows from anywhere.
 */
export function ShortcutToast() {
  const message = useAppStore((s) => s.shortcutToast);
  const visible = useAppStore((s) => s.shortcutToastVisible);

  return (
    <AnimatePresence>
      {visible && message && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.18 }}
          className="pointer-events-none fixed bottom-8 left-1/2 z-[10001] max-w-[70vw] -translate-x-1/2 truncate rounded-[10px] border border-[var(--blue-border)] bg-[rgba(11,16,28,0.92)] px-4 py-2 font-mono text-[11px] tracking-[1px] text-[var(--blue)] shadow-[0_0_24px_rgba(79,168,255,0.2)] backdrop-blur-md"
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
