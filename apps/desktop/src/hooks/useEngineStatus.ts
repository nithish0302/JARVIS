import { useEffect } from "react"
import { useAIStore } from "../stores/useAIStore"
import { checkHealth, getMemoryCount, getSettings } from "../services/jarvisApi"

export function useEngineStatus() {
  const { setStatus, setError, setMemoryCount, setPersonalityMode, setModifier, setAddressPreference, setDailyBriefingEnabled } = useAIStore()

  useEffect(() => {
    // Only used to seed the badge ONCE, before any real response has come
    // back. After that, the badge must reflect the LAST ACTUAL
    // provider/model that answered (set by useJarvisChat's onDone / voice
    // response handler) - re-running this on every poll would silently
    // overwrite an honest post-fallback badge with "whichever provider
    // happens to be first available" every 30s.
    let seeded = false

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
          setError("No AI providers available")
        }
      } catch {
        setStatus("offline")
        setError("JARVIS engine not running")
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
      } catch (err) {
        console.error("Failed to sync settings:", err)
      }
    }

    check()
    checkMemories()
    checkSettings()

    const interval = window.setInterval(check, 30000)
    const memoryInterval = window.setInterval(checkMemories, 60000)

    return () => {
      window.clearInterval(interval)
      window.clearInterval(memoryInterval)
    }
  }, [setStatus, setError, setMemoryCount, setPersonalityMode, setModifier, setAddressPreference, setDailyBriefingEnabled])
}
