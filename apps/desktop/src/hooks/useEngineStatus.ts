import { useEffect } from "react"
import { useAIStore } from "../stores/useAIStore"
import { checkHealth, getMemoryCount } from "../services/jarvisApi"

export function useEngineStatus() {
  const { setStatus, setError, setMemoryCount } = useAIStore()

  useEffect(() => {
    const check = async () => {
      try {
        const health = await checkHealth()
        const ollamaProvider = health.providers.find(
          p => p.name === "ollama"
        )
        if (ollamaProvider?.available) {
          setStatus("idle")
          setError(null)
        } else {
          setStatus("offline")
          setError("Ollama not available")
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

    check()
    checkMemories()
    
    const interval = window.setInterval(check, 30000)
    const memoryInterval = window.setInterval(checkMemories, 60000)
    
    return () => {
      window.clearInterval(interval)
      window.clearInterval(memoryInterval)
    }
  }, [setStatus, setError, setMemoryCount])
}
