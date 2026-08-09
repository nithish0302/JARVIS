import { useEffect, useRef } from "react"
import { useConversationStore } from "../stores/useConversationStore"
import { useAIStore } from "../stores/useAIStore"
import { getConversation } from "../services/jarvisApi"

export function useConversationLoader() {
  const { 
    setConversationId, 
    addMessage, 
    messages 
  } = useConversationStore()
  
  const { status } = useAIStore()
  const hasLoaded = useRef(false)

  // Load when engine becomes ready
  useEffect(() => {
    if (hasLoaded.current) return
    if (messages.length > 0) return
    if (status !== "idle") return

    const savedId = window.localStorage?.getItem(
      "jarvis_conversation_id"
    )
    
    console.log(
      "ConversationLoader: savedId =", savedId,
      "status =", status
    )
    
    if (!savedId) return

    const load = async () => {
      try {
        const history = await getConversation(savedId)
        
        console.log(
          "ConversationLoader: history =", 
          history?.length, "messages"
        )
        
        if (!history || history.length === 0) {
          window.localStorage?.removeItem(
            "jarvis_conversation_id"
          )
          return
        }

        setConversationId(savedId)
        
        history
          .filter((msg: any) => 
            msg.role === "user" || 
            msg.role === "assistant"
          )
          .forEach((msg: any) => {
            addMessage({
              id: window.crypto?.randomUUID() || Math.random().toString(),
              role: msg.role,
              content: msg.content,
              timestamp: msg.timestamp || 
                new Date().toLocaleTimeString(
                  [], { 
                    hour: "2-digit", 
                    minute: "2-digit" 
                  }
                ),
            })
          })
        
        hasLoaded.current = true
        console.log("ConversationLoader: loaded!")
        
      } catch (error) {
        console.error(
          "ConversationLoader: failed", error
        )
        window.localStorage?.removeItem(
          "jarvis_conversation_id"
        )
      }
    }

    load()
    
  }, [status, messages.length, addMessage, setConversationId])
}
