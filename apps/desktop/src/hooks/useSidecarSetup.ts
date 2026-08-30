import { useEffect, useState, useCallback } from "react"
import { invoke } from "@tauri-apps/api/core"
import { listen } from "@tauri-apps/api/event"

export type SidecarSetupStage =
  | "idle"
  | "checking"
  | "downloading"
  | "extracting"
  | "verifying"
  | "done"
  | "error"

export interface SidecarSetupProgress {
  stage: SidecarSetupStage
  percent: number
  message: string
}

const DEFAULT_PROGRESS: SidecarSetupProgress = { stage: "idle", percent: 0, message: "" }

/**
 * Tracks first-run download/extract progress for the jarvis-engine
 * sidecar's `_internal` runtime (see src-tauri/src/sidecar_setup.rs).
 * Listens for live `sidecar-setup-progress` events, and also polls the
 * `get_sidecar_setup_status` command once on mount - the Rust side starts
 * this work from a background task spawned in `.setup()`, so on a slow
 * machine it can emit its first event before this hook's listener is
 * registered; the poll catches that race instead of leaving the UI stuck
 * on the "idle" default.
 */
export function useSidecarSetup() {
  const [progress, setProgress] = useState<SidecarSetupProgress>(DEFAULT_PROGRESS)

  useEffect(() => {
    let cancelled = false

    invoke<SidecarSetupProgress>("get_sidecar_setup_status")
      .then((p) => { if (!cancelled) setProgress(p) })
      .catch(() => {})

    const unlistenPromise = listen<SidecarSetupProgress>("sidecar-setup-progress", (event) => {
      if (!cancelled) setProgress(event.payload)
    })

    return () => {
      cancelled = true
      unlistenPromise.then((unlisten) => unlisten())
    }
  }, [])

  const retry = useCallback(() => {
    setProgress({ stage: "checking", percent: 0, message: "Retrying..." })
    invoke("retry_sidecar_setup").catch((e) => {
      setProgress({ stage: "error", percent: 0, message: `Could not retry: ${e}` })
    })
  }, [])

  return { progress, retry }
}
