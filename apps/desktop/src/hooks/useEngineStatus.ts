import { useEffect } from "react"
import { useAIStore } from "../stores/useAIStore"
import { useAppStore } from "../stores/useAppStore"
import { checkHealth, getMemoryCount, getSettings } from "../services/jarvisApi"

export function useEngineStatus() {
  const { setStatus, setError, setMemoryCount, setPersonalityMode, setModifier, setAddressPreference, setDailyBriefingEnabled } = useAIStore()

  useEffect(() => {
    // Latches true the first time an unconfigured install is observed, so
    // the auto-open below fires once per app session rather than yanking
    // the user back to Settings every 30s poll if they navigate away.
    let hasAutoOpenedSettings = false
    // Only used to seed the badge ONCE, before any real response has come
    // back. After that, the badge must reflect the LAST ACTUAL
    // provider/model that answered (set by useJarvisChat's onDone / voice
    // response handler) - re-running this on every poll would silently
    // overwrite an honest post-fallback badge with "whichever provider
    // happens to be first available" every 30s.
    let seeded = false
    // The bundled backend is spawned by the Tauri shell right as the
    // window opens (see src-tauri/src/lib.rs's spawn_engine_sidecar) and
    // can take a while to become reachable - torch/kokoro/whisper import
    // and warm up before uvicorn starts accepting connections. Polling
    // every 30s would leave the UI reading "JARVIS engine not running"
    // for up to 30s of a startup that's actually proceeding normally.
    // This window polls fast instead, and reads as a startup state
    // ("Starting JARVIS engine...") rather than a failure state, until
    // either it connects or a real timeout elapses.
    const STARTUP_GRACE_MS = 45000
    const startedAt = Date.now()
    const inStartupGrace = () => Date.now() - startedAt < STARTUP_GRACE_MS

    const check = async () => {
      try {
        const health = await checkHealth()
        const activeProvider = health.providers.find(p => p.available)

        if (activeProvider) {
          setStatus("idle")
          setError(null)
          if (!seeded) {
            useAIStore.getState().setProvider(activeProvider.name as any)
            useAIStore.getState().setModel(activeProvider.model)
            seeded = true
          }
        } else {
          setStatus("offline")
          setError(
            useAppStore.getState().providerUnconfigured
              ? "No AI provider configured yet — add one in Settings > Providers"
              : "No AI providers available"
          )
        }
      } catch {
        setStatus("offline")
        setError(
          inStartupGrace()
            ? "Starting JARVIS engine..."
            : "JARVIS engine not running"
        )
      }
    }

    const checkMemories = async () => {
      const count = await getMemoryCount()
      setMemoryCount(count)
    }

    const checkSettings = async () => {
      try {
        const settings = await getSettings()
        if (settings.personality_mode) {
          setPersonalityMode(settings.personality_mode as any)
        }
        if (settings.modifier) {
          setModifier(settings.modifier as any)
        }
        // Empty string is a valid, meaningful value here (no address
        // term at all) - check for undefined, not truthiness, so it
        // isn't silently skipped.
        if (settings.address_preference !== undefined) {
          setAddressPreference(settings.address_preference)
        }
        if (settings.daily_briefing_enabled !== undefined) {
          setDailyBriefingEnabled(settings.daily_briefing_enabled)
        }
        useAIStore.getState().setProviderOverride((settings.provider_override as any) ?? null)
        if (settings.fallback_mode) {
          useAIStore.getState().setFallbackMode(settings.fallback_mode)
        }

        // any_provider_configured reflects EITHER source (.env default or
        // a settings-table override) - the four gemini_configured/etc.
        // flags only reflect a live settings-table override, so deriving
        // "unconfigured" from those alone would false-positive for a
        // perfectly working .env-only setup.
        const unconfigured = settings.any_provider_configured === false
        useAppStore.getState().setProviderUnconfigured(unconfigured)

        if (unconfigured && !hasAutoOpenedSettings) {
          hasAutoOpenedSettings = true
          useAppStore.getState().setSettingsInitialSection("providers")
          useAppStore.getState().setView("settings")
        }
      } catch (err) {
        console.error("Failed to sync settings:", err)
      }
    }

    // Settings first (synchronously establishes providerUnconfigured and,
    // on a fresh install, auto-opens Settings > Providers) so the first
    // check() below can already read an accurate providerUnconfigured
    // instead of racing it.
    checkSettings().then(check)
    checkMemories()

    // Fast cadence for the startup window, normal 30s cadence after -
    // reschedules itself each tick rather than running two competing
    // intervals.
    let cancelled = false
    let timeoutId: number
    const scheduleNext = () => {
      if (cancelled) return
      timeoutId = window.setTimeout(async () => {
        await check()
        scheduleNext()
      }, inStartupGrace() ? 1500 : 30000)
    }
    scheduleNext()

    const memoryInterval = window.setInterval(checkMemories, 60000)

    return () => {
      cancelled = true
      window.clearTimeout(timeoutId)
      window.clearInterval(memoryInterval)
    }
  }, [setStatus, setError, setMemoryCount, setPersonalityMode, setModifier, setAddressPreference, setDailyBriefingEnabled])
}
