import { useConversationStore } from "../stores/useConversationStore"
import { useAIStore } from "../stores/useAIStore"
import { sendMessageStream } from "../services/jarvisApi"
import type { Message } from "../types/chat.types"

export function useJarvisChat() {
  const { 
    messages, 
    addMessage, 
    setTyping,
    currentConversationId,
    setConversationId 
  } = useConversationStore()
  
  const { 
    provider, 
    model, 
    setStatus, 
    setError 
  } = useAIStore()

  const sendUserMessage = async (text: string) => {
    if (!text.trim()) return

    const userMessage: Message = {
      id: window.crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString(
        [], { hour: "2-digit", minute: "2-digit" }
      ),
    }
    addMessage(userMessage)
    setTyping(true)
    setStatus("streaming")
    setError(null)

    // Create placeholder for streaming message
    const streamingId = window.crypto.randomUUID()
    useConversationStore.getState().startStreaming(streamingId)

    try {
      await sendMessageStream(
        {
          message: text,
          conversation_id: currentConversationId,
          provider,
          model,
        },
        // onToken — append each word
        (token) => {
          useConversationStore.getState().appendStreamToken(token)
        },
        // onDone — add complete message
        (convId, fullResponse) => {
          useConversationStore.getState().finishStreaming()
          if (!currentConversationId) {
            setConversationId(convId)
          }
          const assistantMessage: Message = {
            id: streamingId,
            role: "assistant",
            content: fullResponse,
            timestamp: new Date().toLocaleTimeString(
              [], { 
                hour: "2-digit", 
                minute: "2-digit" 
              }
            ),
          }
          addMessage(assistantMessage)
          setStatus("idle")
          setTyping(false)
        },
        // onError
        (error) => {
          useConversationStore.getState().finishStreaming()
          const errorMessage: Message = {
            id: window.crypto.randomUUID(),
            role: "assistant",
            content:
              "I apologize, I encountered an error. " +
              "Please try again.",
            timestamp: new Date().toLocaleTimeString(
              [], { 
                hour: "2-digit", 
                minute: "2-digit" 
              }
            ),
          }
          addMessage(errorMessage)
          setStatus("error")
          setError(error)
          setTyping(false)
        }
      )
    } catch {
      useConversationStore.getState().finishStreaming()
      setStatus("error")
      setTyping(false)
    }
  }

  return { 
    messages, 
    sendUserMessage,
    isTyping: useConversationStore(s => s.isTyping)
  }
}
