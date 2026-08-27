import { useRef, useEffect } from "react"
import { useConversationStore } from "../stores/useConversationStore"
import { useAIStore } from "../stores/useAIStore"
import { sendMessageStream, connectVoiceWebSocket } from "../services/jarvisApi"
import type { Message } from "../types/chat.types"
import { parseUIActions } from "../utils/uiActionParser"
import { executeUIActions } from "../utils/uiActionExecutor"
import { isVoiceSafe } from "../utils/actionSafety"
import { runConfirmedAction } from "../utils/confirmedActions"
import { useAppStore } from "../stores/useAppStore"
import { useMicLevelStore } from "../stores/useMicLevelStore"

/**
 * Decides whether an incoming voice turn's conversation_id (routes.py has
 * always included this in the voice_input/voice_response broadcasts - see
 * the live diagnostic that confirmed the backend groups every turn of a
 * continuous session under one id) belongs to the conversation already
 * open in the UI, starts a fresh one, or supersedes a stale one.
 *
 * Three cases, matching what the backend actually does:
 *   - No conversation open yet -> this voice turn IS the start of one;
 *     adopt its id as the active thread.
 *   - Already showing this exact id -> same session, same thread, nothing
 *     to do (covers the common case: voice_input and voice_response of the
 *     same turn each call this, so the second call is always a no-op).
 *   - Showing a DIFFERENT id -> the backend generated a new id, which only
 *     happens after continuous mode actually exited (timeout, exit phrase,
 *     or "go to sleep") and a fresh wake word started a new session, or the
 *     previously-open thread was an unrelated text chat. Either way this is
 *     a genuinely new conversation, not a continuation - clear the old
 *     thread out of view and switch to the new one rather than appending.
 *
 * Idempotent and cheap to call from both the voice_input and voice_response
 * handlers - exactly one of the three branches ever actually changes state.
 */
export function reconcileVoiceConversation(conversationId: string | null | undefined) {
  if (!conversationId) return

  const convoStore = useConversationStore.getState()
  const current = convoStore.currentConversationId

  if (current === conversationId) {
    return
  }

  if (!current) {
    convoStore.setConversationId(conversationId)
  } else {
    convoStore.clearConversation()
    convoStore.setConversationId(conversationId)
  }
  // Sidebar refresh is handled uniformly after every addMessage() call in
  // the voice_input/voice_response handlers below (covers create, switch,
  // AND plain append in one place) - no separate bump needed here.
}

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
  const lastVoiceSeqRef = useRef<number>(-1)

  // Connect to voice WebSocket with cleanup and sequence validation
  useEffect(() => {
    const disconnect = connectVoiceWebSocket(
      // Voice input received - reconcile which conversation this turn
      // belongs to BEFORE adding the message, so it lands in the right
      // (possibly just-switched) message list rather than the stale one.
      (text: string, seq?: number, conversationId?: string | null) => {
        if (seq !== undefined) {
          if (seq <= lastVoiceSeqRef.current) {
            console.warn(`[WS] Discarding stale voice_input event (seq ${seq} <= ${lastVoiceSeqRef.current})`)
            return
          }
          lastVoiceSeqRef.current = seq
        }
        reconcileVoiceConversation(conversationId)
        const userMessage: Message = {
          id: crypto.randomUUID(),
          role: "user",
          content: `🎤 ${text}`,
          timestamp: new Date().toLocaleTimeString(
            [], {hour:"2-digit", minute:"2-digit"}
          )
        }
        addMessage(userMessage)
        // The sidebar's preview text / relative timestamp for this
        // conversation just went stale server-side (save_message() already
        // ran before this broadcast fired) - bump so it refetches while
        // the panel is open, without the user having to reopen it.
        useAppStore.getState().bumpConversationsVersion()
      },
      // Voice response received - add as assistant message
      (text: string, seq?: number, meta?: { providerUsed: string | null, modelUsed: string | null, fallbackOccurred: boolean, failedProvider: string | null, conversationId?: string | null }) => {
        if (seq !== undefined) {
          if (seq <= lastVoiceSeqRef.current) {
            console.warn(`[WS] Discarding stale voice_response event (seq ${seq} <= ${lastVoiceSeqRef.current})`)
            return
          }
          lastVoiceSeqRef.current = seq
        }
        // Normally a no-op here - voice_input for the same turn already
        // reconciled this exact id. Kept as a defensive second check for
        // the case a voice_response arrives without its voice_input having
        // been seen (e.g. the WS reconnected between the two events).
        reconcileVoiceConversation(meta?.conversationId)

        // Reflect the ACTUAL provider/model that answered - not a static
        // config value - and surface a fallback notice if one occurred.
        if (meta?.providerUsed && !["direct", "asking", "override_unavailable", "error"].includes(meta.providerUsed)) {
          useAIStore.getState().setProvider(meta.providerUsed as any)
        }
        if (meta?.modelUsed && !["direct", "asking", "unavailable", "error"].includes(meta.modelUsed)) {
          useAIStore.getState().setModel(meta.modelUsed)
        }
        useAIStore.getState().setLastFallback(!!meta?.fallbackOccurred, meta?.failedProvider ?? null)
        if (meta?.fallbackOccurred && meta.failedProvider && meta.providerUsed) {
          useAppStore.getState().showFallbackToast(
            `${meta.failedProvider} had an issue — switched to ${meta.providerUsed}`
          )
        }

        // Strip UI_ACTION tags before displaying
        const { cleanText, actions } = parseUIActions(text)
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: cleanText,
          timestamp: new Date().toLocaleTimeString(
            [], {hour:"2-digit", minute:"2-digit"}
          )
        }
        addMessage(assistantMessage)
        useAppStore.getState().bumpConversationsVersion()
        setStatus("idle")

        if (actions.length > 0) {
          // ALLOWLIST, not blocklist. This was a Set of two blocked
          // actions, which meant every action added afterwards —
          // send_email, create_event, create_github_issue — was
          // executable straight off a transcript by default. An action
          // now has to be explicitly known-safe (see isVoiceSafe) to run
          // without confirmation; anything else is deferred to the same
          // confirm step the backend uses, so a new plugin's destructive
          // action is unsafe-by-default rather than the reverse.
          const safeActions = actions.filter(a => isVoiceSafe(a.type))
          const deferredActions = actions.filter(a => !isVoiceSafe(a.type))

          if (safeActions.length > 0) {
            executeUIActions(safeActions)
          }

          // Only one action can await confirmation at a time, so take the
          // first and tell the user what's waiting. The ConfirmationButtons
          // component renders off pendingCommand, which is what makes this
          // reachable from voice at all — a spoken "yes" goes back through
          // /voice/input as a fresh utterance, not as a confirmation.
          if (deferredActions.length > 0) {
            const [pending, ...ignored] = deferredActions
            console.warn(
              `[Voice] Action "${pending.type}" requires confirmation — deferring`,
              pending.payload
            )
            if (ignored.length > 0) {
              console.warn(
                "[Voice] Additional actions dropped while awaiting confirmation:",
                ignored.map(a => a.type)
              )
            }
            useAppStore.getState().setPendingCommand(
              pending.payload
                ? `${pending.type}:${pending.payload}`
                : pending.type
            )
            useAppStore.getState().showActionFeedback(
              "Confirm to continue."
            )
          }
        }
      },
      // Voice status received - sync orb
      (status: string, seq?: number) => {
        if (seq !== undefined) {
          if (seq <= lastVoiceSeqRef.current) {
            console.warn(`[WS] Discarding stale voice_status event '${status}' (seq ${seq} <= ${lastVoiceSeqRef.current})`)
            return
          }
          lastVoiceSeqRef.current = seq
        }
        const { setVoiceStatus } = useAIStore.getState()
        setVoiceStatus(status as any)
      },
      // Audio level received - feed the mic waveform indicator
      (level: number) => {
        useMicLevelStore.getState().pushLevel(level)
      }
    )

    return () => {
      disconnect()
    }
  }, [addMessage, setStatus])

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

    // Handle confirmation responses
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
      const cmdType = colonIdx === -1
        ? pendingCommand
        : pendingCommand.substring(0, colonIdx)
      const cmdPayload = colonIdx === -1
        ? ""
        : pendingCommand.substring(colonIdx + 1)

      runConfirmedAction(cmdType, cmdPayload, addMessage)
        .finally(() => setPendingCommand(null))

      return // Don't send to AI
    }

    // Handle cancellation
    if (pendingCommand && ["no", "cancel", "stop"].includes(text.toLowerCase().trim())) {
      const userMessage: Message = {
        id: window.crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date().toLocaleTimeString(
          [], { hour: "2-digit", minute: "2-digit" }
        ),
      }
      addMessage(userMessage)

      addMessage({
        id: window.crypto.randomUUID(),
        role: "assistant",
        content: "Action cancelled, sir.",
        timestamp: new Date().toLocaleTimeString(
          [], { hour: "2-digit", minute: "2-digit" }
        ),
      })

      setPendingCommand(null)
      return // Don't send to AI
    }

    // If user sends a different message while pending command exists,
    // clear the pending command (timeout/user changed mind)
    if (pendingCommand) {
      console.log("[JARVIS] Clearing stale pending command due to new user message")
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
        (convId, fullResponse, sources = [], providerUsed = "unknown", modelUsed = "unknown", fallbackOccurred = false, failedProvider = null) => {
          try {
            useConversationStore.getState().finishStreaming()

            if (!currentConversationId && convId) {
              setConversationId(convId)
            }

            // Update AI store with the ACTUAL provider/model that answered -
            // this is what makes the Topbar badge honest instead of a
            // static config value, and it visibly changes on a fallback.
            const unresolvedProviders = ["unknown", "asking", "override_unavailable", "error"]
            if (!unresolvedProviders.includes(providerUsed)) {
              useAIStore.getState().setProvider(providerUsed as any)
            }
            if (modelUsed !== "unknown" && modelUsed !== "asking" && modelUsed !== "unavailable") {
              useAIStore.getState().setModel(modelUsed)
            }
            useAIStore.getState().setLastFallback(fallbackOccurred, failedProvider)
            if (fallbackOccurred && failedProvider) {
              useAppStore.getState().showFallbackToast(
                `${failedProvider} had an issue — switched to ${providerUsed}`
              )
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
