import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "../../../stores/useAppStore";

export function ActionFeedback() {
  const { actionFeedback, actionFeedbackVisible } = useAppStore();

  return (
    <div className="h-[20px] flex items-center justify-center mt-2">
      <AnimatePresence>
        {actionFeedbackVisible && actionFeedback && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 1 } }}
            transition={{ duration: 0.3 }}
            className="text-[var(--color-cyan)] font-display text-[13px] font-semibold tracking-[1px] text-center"
          >
            {actionFeedback}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
