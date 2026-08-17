import { useRef, useEffect } from "react"
import { useConversationStore } from "../stores/useConversationStore"
import { useAIStore } from "../stores/useAIStore"
import { sendMessageStream } from "../services/jarvisApi"
import type { Message } from "../types/chat.types"
import { parseUIActions } from "../utils/uiActionParser"
import { executeUIActions } from "../utils/uiActionExecutor"
import { useAppStore } from "../stores/useAppStore"
import { executePowerShell } from "../services/systemApi"

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

  const uiActionTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (uiActionTimerRef.current) {
        clearTimeout(uiActionTimerRef.current)
      }
    }
  }, [])

  const sendUserMessage = async (text: string) => {
    if (!text.trim()) return

    const { pendingCommand, setPendingCommand } = useAppStore.getState()

    if (pendingCommand && 
        ["yes","confirm","ok","do it","go ahead","sure","proceed"]
          .includes(text.toLowerCase().trim())) {
      
      const userMessage: Message = {
        id: window.crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date().toLocaleTimeString(
          [], { hour: "2-digit", minute: "2-digit" }
        ),
      }
      addMessage(userMessage)

      const colonIdx = pendingCommand.indexOf(":")
      const cmdType = pendingCommand.substring(0, colonIdx)
      const cmdPayload = pendingCommand.substring(colonIdx + 1)
      
      if (cmdType === "delete_file") {
        import("../services/systemApi").then(s => {
          s.deleteFile(cmdPayload, true)
            .then((result: string) => {
              addMessage({
                id: window.crypto.randomUUID(),
                role: "assistant",
                content: `✅ ${result}`,
                timestamp: new Date()
                  .toLocaleTimeString([],{
                    hour:"2-digit",
                    minute:"2-digit"
                  })
              })
            })
            .catch((err: Error) => {
              addMessage({
                id: window.crypto.randomUUID(),
                role: "assistant", 
                content: `❌ Failed: ${err.message}`,
                timestamp: new Date()
                  .toLocaleTimeString([],{
                    hour:"2-digit",
                    minute:"2-digit"
                  })
              })
            })
        })
      } else {
        executePowerShell(pendingCommand, true)
          .then(result => {
            addMessage({
              id: window.crypto.randomUUID(),
              role: "assistant",
              content: `Done. Command output:\n${result}`,
              timestamp: new Date().toLocaleTimeString(
                [], {hour:"2-digit",minute:"2-digit"}
              )
            })
          })
          .catch(err => {
            addMessage({
              id: window.crypto.randomUUID(),
              role: "assistant",
              content: `Failed. Error:\n${err}`,
              timestamp: new Date().toLocaleTimeString(
                [], {hour:"2-digit",minute:"2-digit"}
              )
            })
          })
      }
        
      setPendingCommand(null)
      return // Don't send to AI
    } else if (pendingCommand && ["no", "cancel", "stop"].includes(text.toLowerCase().trim())) {
      setPendingCommand(null)
    }

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
        // onSearchStarted
        (query) => {
          useConversationStore.getState().setSearching(true, query)
        },
        // onSearchComplete
        () => {
          useConversationStore.getState().setSearching(false)
        },
        // onToken — append each word
        (token) => {
          useConversationStore.getState().appendStreamToken(token)
        },
        // onDone — add complete message
        (convId, fullResponse, sources = [], providerUsed = "unknown", modelUsed = "unknown") => {
          try {
            useConversationStore.getState().finishStreaming()

            if (!currentConversationId && convId) {
              setConversationId(convId)
            }

            // Update AI store with actual provider/model used
            if (providerUsed !== "unknown") {
              useAIStore.getState().setProvider(providerUsed as any)
            }
            if (modelUsed !== "unknown") {
              useAIStore.getState().setModel(modelUsed)
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
              if (uiActionTimerRef.current) {
                clearTimeout(uiActionTimerRef.current)
              }
              uiActionTimerRef.current = setTimeout(() => {
                executeUIActions(actions)
                uiActionTimerRef.current = null
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

  // Listen for confirmation button events
  useEffect(() => {
    const handleConfirm = (e: Event) => {
      const customEvent = e as CustomEvent
      const response = customEvent.detail.response
      if (response === "yes") {
        sendUserMessage("yes")
      } else {
        sendUserMessage("cancel")
        // Add cancel message to chat
        addMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Action cancelled, sir.",
          timestamp: new Date().toLocaleTimeString(
            [], {hour:"2-digit",minute:"2-digit"}
          )
        })
      }
    }

    window.addEventListener(
      "jarvis-confirm",
      handleConfirm as EventListener
    )
    return () => {
      window.removeEventListener(
        "jarvis-confirm",
        handleConfirm as EventListener
      )
    }
  }, [sendUserMessage, addMessage])

  return {
    messages,
    sendUserMessage,
    isTyping: useConversationStore(s => s.isTyping),
    streamingMessageId,
    streamingContent,
    streamingSearchQuery
  }
}
