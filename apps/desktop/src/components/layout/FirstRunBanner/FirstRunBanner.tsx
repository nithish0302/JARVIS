import { AnimatePresence, motion } from "framer-motion";
import { useAppStore } from "../../../stores/useAppStore";

/**
 * Persistent, dismissable-by-navigation prompt shown whenever no AI
 * provider has any key/host configured (useEngineStatus sets
 * providerUnconfigured from GET /settings). useEngineStatus also
 * auto-opens Settings > Providers once on first detection - this banner
 * covers everything after that: it stays visible on every other view
 * until a provider is actually configured, so the path back to Settings
 * is never more than a click away.
 */
export function FirstRunBanner() {
  const unconfigured = useAppStore((s) => s.providerUnconfigured);
  const view = useAppStore((s) => s.view);
  const setView = useAppStore((s) => s.setView);
  const setSettingsInitialSection = useAppStore((s) => s.setSettingsInitialSection);

  const openProviders = () => {
    setSettingsInitialSection("providers");
    setView("settings");
  };

  return (
    <AnimatePresence>
      {unconfigured && view !== "settings" && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
          className="fixed left-1/2 top-4 z-[10001] flex -translate-x-1/2 items-center gap-3 rounded-[10px] border border-[var(--color-amber,#f59e0b)] bg-[rgba(20,14,4,0.92)] px-4 py-2 font-mono text-[11px] tracking-[0.5px] text-[var(--color-amber,#f59e0b)] shadow-[0_0_24px_rgba(245,158,11,0.2)] backdrop-blur-md"
        >
          <span>⚠ No AI provider configured yet.</span>
          <button
            onClick={openProviders}
            className="pointer-events-auto rounded border border-[var(--color-amber,#f59e0b)] px-2 py-0.5 text-[11px] uppercase tracking-[0.5px] text-[var(--color-amber,#f59e0b)] transition-colors hover:bg-[var(--color-amber,#f59e0b)] hover:text-black"
          >
            Open Settings
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
