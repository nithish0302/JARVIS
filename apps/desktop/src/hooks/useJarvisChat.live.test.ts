// @vitest-environment node
//
// jsdom's WebSocket shim (vitest's default environment) throws internally
// ("event argument must be an instance of Event") when it wraps a real
// connection to an external ws:// server - a jsdom/undici incompatibility,
// confirmed separately: a bare `node -e "new WebSocket(...)"` against this
// same server connects and closes cleanly. This file needs a real socket
// to a real server, not a DOM, so it runs under Node's own environment
// instead. The store modules reference `window.localStorage` defensively
// (`window.localStorage?.setItem`) - window itself doesn't exist in bare
// Node, so give it a minimal stand-in before importing anything that
// might touch it.
if (typeof window === "undefined") {
  const store = new Map<string, string>()
  ;(globalThis as any).window = {
    localStorage: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => { store.set(k, v) },
      removeItem: (k: string) => { store.delete(k) },
    },
  }
}

import { describe, it, expect, beforeEach } from "vitest"
import { connectVoiceWebSocket } from "../services/jarvisApi"
import { reconcileVoiceConversation } from "./useJarvisChat"
import { useConversationStore } from "../stores/useConversationStore"

/**
 * LIVE integration check, not part of the CI-gating suite - same
 * separation as services/jarvis-engine/tests/run_live_test.py. Skipped by
 * default; requires the real jarvis-engine running on localhost:8765
 * (`uv run python start.py` from services/jarvis-engine).
 *
 * Everything else in this file's sibling test (useJarvisChat.test.ts)
 * exercises reconcileVoiceConversation() against synthetic ids. This test
 * instead drives it with REAL WebSocket broadcasts from the REAL running
 * engine, closing the loop the task asked for: proof that what the
 * backend actually sends over /ws/voice (with a genuine conversation_id
 * threaded through 3 real /voice/input calls) produces the correct
 * grouped-vs-separate state in the frontend store, using the exact
 * connectVoiceWebSocket() parsing code and reconcileVoiceConversation()
 * logic the real app runs - not a mock of either.
 *
 * To run: LIVE_ENGINE=1 npx vitest run src/hooks/useJarvisChat.live.test.ts
 */
// globalThis.process rather than a bare `process` reference - this
// project's tsconfig has no Node lib/@types/node (it's a Vite frontend),
// so the bare global identifier doesn't typecheck even though it exists
// at runtime under vitest's node environment.
const LIVE = (globalThis as any).process?.env?.LIVE_ENGINE === "1"
const ENGINE_URL = "http://localhost:8765"

async function postVoiceInput(text: string, conversationId?: string) {
  const body: Record<string, string> = { text }
  if (conversationId) body.conversation_id = conversationId
  const res = await fetch(`${ENGINE_URL}/voice/input`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`/voice/input HTTP ${res.status}`)
  return res.json()
}

function waitForEvents(count: number, timeoutMs = 60000): Promise<{
  type: string
  conversationId: string | null | undefined
}[]> {
  return new Promise((resolve, reject) => {
    const seen: { type: string; conversationId: string | null | undefined }[] = []
    const timer = setTimeout(() => {
      disconnect()
      reject(new Error(`Timed out waiting for ${count} WS events, got ${seen.length}`))
    }, timeoutMs)

    const disconnect = connectVoiceWebSocket(
      (_text, _seq, conversationId) => {
        seen.push({ type: "voice_input", conversationId })
        reconcileVoiceConversation(conversationId)
        useConversationStore.getState().addMessage({
          id: crypto.randomUUID(), role: "user", content: _text, timestamp: ""
        })
        if (seen.length >= count) { clearTimeout(timer); disconnect(); resolve(seen) }
      },
      (_text, _seq, meta) => {
        seen.push({ type: "voice_response", conversationId: meta?.conversationId })
        reconcileVoiceConversation(meta?.conversationId)
        useConversationStore.getState().addMessage({
          id: crypto.randomUUID(), role: "assistant", content: _text, timestamp: ""
        })
        if (seen.length >= count) { clearTimeout(timer); disconnect(); resolve(seen) }
      },
      () => {},
    )
  })
}

beforeEach(() => {
  useConversationStore.setState({
    messages: [], currentConversationId: null, currentConversationTitle: null
  })
})

describe.skipIf(!LIVE)("live: real backend WS -> frontend conversation grouping", () => {
  it(
    "TASK TEST 1: a real 3-turn continuous session groups under ONE conversation in the store",
    async () => {
      const cid = `live-test-${crypto.randomUUID()}`
      const eventsPromise = waitForEvents(6) // 3 turns x (voice_input + voice_response)

      await postVoiceInput("what is two plus two", cid)
      await postVoiceInput("what about three plus three", cid)
      await postVoiceInput("thank you", cid)

      const events = await eventsPromise

      expect(events.every(e => e.conversationId === cid)).toBe(true)
      expect(useConversationStore.getState().currentConversationId).toBe(cid)
      expect(useConversationStore.getState().messages.length).toBe(6)
    },
    90000
  )

  it(
    "TASK TEST 2: a genuinely different conversation_id starts a separate thread, not merged",
    async () => {
      const cidA = `live-test-${crypto.randomUUID()}`
      const cidB = `live-test-${crypto.randomUUID()}`

      const firstSession = waitForEvents(2)
      await postVoiceInput("session A turn one", cidA)
      await firstSession
      expect(useConversationStore.getState().currentConversationId).toBe(cidA)
      expect(useConversationStore.getState().messages.length).toBe(2)

      const secondSession = waitForEvents(2)
      await postVoiceInput("session B turn one", cidB)
      await secondSession

      const state = useConversationStore.getState()
      expect(state.currentConversationId).toBe(cidB)
      // Switched, not merged: exactly this session's 2 messages, not 4.
      expect(state.messages.length).toBe(2)
      // Only the user turn echoes the literal text posted - the other
      // message is the LLM's own reply, whatever it chose to say back.
      // Checking role, not content pattern, on that one.
      const [userMsg, assistantMsg] = state.messages
      expect(userMsg.role).toBe("user")
      expect(userMsg.content).toContain("session B")
      expect(assistantMsg.role).toBe("assistant")
    },
    90000
  )
})
