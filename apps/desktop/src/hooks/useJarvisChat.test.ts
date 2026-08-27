import { describe, it, expect, beforeEach } from "vitest"
import { reconcileVoiceConversation } from "./useJarvisChat"
import { useConversationStore } from "../stores/useConversationStore"
import { useAppStore } from "../stores/useAppStore"

/**
 * Regression coverage for the bug this fix addresses: routes.py has always
 * included conversation_id in the voice_input/voice_response WebSocket
 * broadcasts, but nothing on the frontend read it, so a real 3-turn
 * continuous voice session (proven correct server-side - one
 * conversation_id, one conversations row, three messages) showed up as
 * three separate entries in the desktop app's Conversations sidebar
 * because the UI had no way to know the turns belonged together.
 */

function resetStores() {
  useConversationStore.setState({
    messages: [],
    currentConversationId: null,
    currentConversationTitle: null,
  })
  useAppStore.setState({ conversationsVersion: 0 })
  window.localStorage?.removeItem("jarvis_conversation_id")
}

beforeEach(() => {
  resetStores()
})

describe("reconcileVoiceConversation", () => {
  it("adopts the incoming id when no conversation is open (first turn of a fresh session)", () => {
    reconcileVoiceConversation("conv-A")

    expect(useConversationStore.getState().currentConversationId).toBe("conv-A")
  })

  it("does nothing when the incoming id already matches the active conversation (turn 2, 3, ... of the same session)", () => {
    reconcileVoiceConversation("conv-A")
    useConversationStore.getState().addMessage({
      id: "1", role: "user", content: "turn 1", timestamp: "10:00"
    })

    reconcileVoiceConversation("conv-A")

    // Same id, same thread - messages must NOT be cleared out from under
    // an in-progress conversation.
    expect(useConversationStore.getState().currentConversationId).toBe("conv-A")
    expect(useConversationStore.getState().messages).toHaveLength(1)
  })

  it("THE 3-TURN REGRESSION TEST: three turns sharing one conversation_id never trigger a switch after the first", () => {
    const ids = ["conv-session-1", "conv-session-1", "conv-session-1"]
    for (const id of ids) {
      reconcileVoiceConversation(id)
    }

    expect(useConversationStore.getState().currentConversationId).toBe("conv-session-1")
  })

  it("switches to a genuinely new conversation when the incoming id differs from the active one (new wake session after exit)", () => {
    reconcileVoiceConversation("conv-A")
    useConversationStore.getState().addMessage({
      id: "1", role: "assistant", content: "old session reply", timestamp: "10:00"
    })

    reconcileVoiceConversation("conv-B")

    const state = useConversationStore.getState()
    expect(state.currentConversationId).toBe("conv-B")
    // The old session's messages must not bleed into the new one.
    expect(state.messages).toHaveLength(0)
  })

  it("REGRESSION GUARD: never merges two genuinely different voice sessions into one giant thread", () => {
    reconcileVoiceConversation("session-1")
    useConversationStore.getState().addMessage({
      id: "1", role: "user", content: "first session, turn 1", timestamp: "10:00"
    })
    useConversationStore.getState().addMessage({
      id: "2", role: "assistant", content: "first session reply", timestamp: "10:00"
    })

    // "Go to sleep" happens; backend later hands out a new id for a fresh
    // wake session.
    reconcileVoiceConversation("session-2")
    useConversationStore.getState().addMessage({
      id: "3", role: "user", content: "second session, turn 1", timestamp: "10:05"
    })

    const state = useConversationStore.getState()
    expect(state.currentConversationId).toBe("session-2")
    expect(state.messages).toHaveLength(1)
    expect(state.messages[0].content).toBe("second session, turn 1")
    // The first session's turns are gone from the VIEW (not merged in) -
    // they remain correctly persisted server-side under session-1, which
    // is exactly what /conversations lists them under.
    expect(state.messages.some(m => m.content.includes("first session"))).toBe(false)
  })

  it("is a no-op for an undefined/null/empty conversation_id (defensive - should never happen if the backend is behaving)", () => {
    reconcileVoiceConversation("conv-A")
    reconcileVoiceConversation(undefined)
    reconcileVoiceConversation(null)
    reconcileVoiceConversation("")

    expect(useConversationStore.getState().currentConversationId).toBe("conv-A")
  })
})
