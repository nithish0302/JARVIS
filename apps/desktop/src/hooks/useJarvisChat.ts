import { useRef } from "react"
import { useConversationStore } from "../stores/useConversationStore"
import { useAIStore } from "../stores/useAIStore"
import { sendMessageStream } from "../services/jarvisApi"
import type { Message } from "../types/chat.types"
import { parseUIActions } from "../utils/uiActionParser"
import { executeUIActions } from "../utils/uiActionExecutor"

export function useJarvisChat() {
  const { 
    messages, 
    addMessage, 
    setTyping,
    currentConversationId,
    setConversationId,
    streamingMessageId,
    streamingContent,
    streamingSearchQuery
  } = useConversationStore()
  
  const { 
    provider, 
    model, 
    setStatus, 
    setError 
  } = useAIStore()
  
  const searchMetaRef = useRef<{
    searchPerformed: boolean,
    searchQuery: string,
    sources: any[]
  }>({
    searchPerformed: false,
    searchQuery: "",
    sources: []
  })

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
        // onMeta — update streaming search query
        (meta) => {
          searchMetaRef.current = {
            searchPerformed: meta.searchPerformed,
            searchQuery: meta.searchQuery,
            sources: meta.sources
          }
          if (meta.searchQuery) {
            useConversationStore.getState().setStreamingMeta(meta.searchQuery)
          }
        },
        // onToken — append each word
        (token) => {
          useConversationStore.getState().appendStreamToken(token)
        },
        // onDone — add complete message
        (convId, fullResponse, sources = []) => {
          try {
            useConversationStore.getState().finishStreaming()

            if (!currentConversationId && convId) {
              setConversationId(convId)
            }

            // Parse UI actions FIRST
            const { cleanText, actions } = parseUIActions(
              fullResponse || ""
            )

            // Build message with CLEAN text
            const assistantMessage: Message = {
              id: streamingId,
              role: "assistant" as const,
              content: cleanText,
              timestamp: new Date().toLocaleTimeString(
                [], { hour: "2-digit", minute: "2-digit" }
              ),
              searchPerformed: sources.length > 0,
              searchQuery: searchMetaRef.current
                ?.searchQuery || "",
              sources: Array.isArray(sources)
                ? sources.map(s => ({
                    title: String(s?.title || ""),
                    url: String(s?.url || ""),
                    snippet: String(s?.snippet || ""),
                    source: String(s?.source || "")
                  }))
                : [],
            }

            addMessage(assistantMessage)
            setStatus("idle")
            setTyping(false)

            // Execute UI actions after message renders
            if (actions.length > 0) {
              setTimeout(() => {
                executeUIActions(actions)
              }, 500)
            }

            // Reset search meta
            searchMetaRef.current = {
              searchPerformed: false,
              searchQuery: "",
              sources: []
            }

          } catch (error) {
            console.error("onDone error:", error)
            const fallbackMessage: Message = {
              id: streamingId,
              role: "assistant" as const,
              content: fullResponse || "",
              timestamp: new Date().toLocaleTimeString(
                [], { hour: "2-digit", minute: "2-digit" }
              ),
            }
            addMessage(fallbackMessage)
            setStatus("idle")
            setTyping(false)
          }
        },
        // onError
        (error: string) => {
          try {
            useConversationStore.getState().finishStreaming()
            
            // Only add error message if we have no
            // streaming content yet
            const currentContent = useConversationStore.getState().streamingContent
            if (!currentContent || 
                currentContent.trim().length === 0) {
              const errorMessage: Message = {
                id: window.crypto.randomUUID(),
                role: "assistant" as const,
                content:
                  "I apologize, I am unable to connect. " +
                  "Please ensure the JARVIS engine is running.",
                timestamp: new Date().toLocaleTimeString(
                  [], { hour: "2-digit", minute: "2-digit" }
                ),
              }
              addMessage(errorMessage)
            }
            
            setStatus("error")
            setError(error)
            setTyping(false)
          } catch (e) {
            console.error("onError handler failed:", e)
            setStatus("error")
            setTyping(false)
          }
        }
      )
    } catch (error) {
      console.error("sendUserMessage failed:", error)
      useConversationStore.getState().finishStreaming()
      setStatus("error")
      setTyping(false)
    }
  }

  return { 
    messages, 
    sendUserMessage,
    isTyping: useConversationStore(s => s.isTyping),
    streamingMessageId,
    streamingContent,
    streamingSearchQuery
  }
}
