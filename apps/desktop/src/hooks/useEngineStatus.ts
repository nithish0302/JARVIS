import { useEffect } from "react"
import { useAIStore } from "../stores/useAIStore"
import { checkHealth, getMemoryCount, getSettings } from "../services/jarvisApi"

export function useEngineStatus() {
  const { setStatus, setError, setMemoryCount, setPersonalityMode, setModifier, setAddressPreference, setDailyBriefingEnabled } = useAIStore()

  useEffect(() => {
    const check = async () => {
      try {
        const health = await checkHealth()
        const activeProvider = health.providers.find(p => p.available)
        
        if (activeProvider) {
          setStatus("idle")
          setError(null)
          // Ensure store typings are respected while syncing
          useAIStore.getState().setProvider(activeProvider.name as any)
          useAIStore.getState().setModel(activeProvider.model)
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
