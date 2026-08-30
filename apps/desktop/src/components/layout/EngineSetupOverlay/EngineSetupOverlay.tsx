import { AnimatePresence, motion } from "framer-motion"
import { useSidecarSetup } from "../../../hooks/useSidecarSetup"

const STAGE_LABEL: Record<string, string> = {
  checking: "Preparing setup...",
  downloading: "Downloading JARVIS engine components...",
  extracting: "Extracting JARVIS engine components...",
  verifying: "Verifying installation...",
}

/**
 * Full-screen blocking overlay shown only on first run, while
 * src-tauri/src/sidecar_setup.rs downloads and extracts the backend's
 * `_internal` runtime (no longer bundled into the installer - see that
 * file for why). Without this the app would sit on a "JARVIS engine not
 * running" message for minutes with no indication anything is happening.
 * Hidden once the runtime is present ("done") or before setup has begun
 * ("idle" - e.g. on every normal launch after the first).
 */
export function EngineSetupOverlay() {
  const { progress, retry } = useSidecarSetup()
  const visible = progress.stage !== "idle" && progress.stage !== "done"

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[20000] flex flex-col items-center justify-center gap-5 bg-[rgba(6,8,12,0.96)] px-6 text-center backdrop-blur-md"
        >
          <div className="font-mono text-[13px] tracking-[1px] text-[var(--color-text-primary,#e5e7eb)]">
            {progress.stage === "error" ? "Setup failed" : "Setting up JARVIS"}
          </div>

          {progress.stage !== "error" ? (
            <>
              <div className="h-1.5 w-[320px] max-w-[80vw] overflow-hidden rounded-full bg-[rgba(255,255,255,0.08)]">
                <motion.div
                  className="h-full rounded-full bg-[var(--color-accent,#38bdf8)]"
                  animate={{ width: `${Math.max(4, Math.min(100, progress.percent))}%` }}
                  transition={{ duration: 0.2 }}
                />
              </div>
              <div className="font-mono text-[11px] text-[var(--color-text-secondary,#9ca3af)]">
                {STAGE_LABEL[progress.stage] ?? progress.message}
                {progress.stage === "downloading" ? ` ${Math.round(progress.percent)}%` : ""}
              </div>
              <div className="max-w-[420px] font-mono text-[10px] text-[var(--color-text-tertiary,#6b7280)]">
                This is a one-time download of the backend runtime (a few GB) - it won't happen again once complete.
              </div>
            </>
          ) : (
            <>
              <div className="max-w-[420px] font-mono text-[11px] text-[var(--color-amber,#f59e0b)]">
                {progress.message || "Something went wrong during setup."}
              </div>
              <button
                onClick={retry}
                className="rounded-[8px] border border-[var(--color-accent,#38bdf8)] bg-[rgba(56,189,248,0.1)] px-4 py-2 font-mono text-[11px] tracking-[0.5px] text-[var(--color-accent,#38bdf8)] transition-colors hover:bg-[rgba(56,189,248,0.2)]"
              >
                Retry
              </button>
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
