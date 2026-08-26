/* eslint-disable no-unused-vars */
import { SearchSource } from "../types/chat.types"
export const JARVIS_ENGINE_URL = "http://localhost:8765"

export interface ChatRequest {
  message: string
  conversation_id: string | null
  provider: string
  model: string
}

export interface ChatResponse {
  response: string
  conversation_id: string
  provider_used: string
  model_used: string
  search_performed: boolean
  search_query: string
  sources: SearchSource[]
  fallback_occurred: boolean
  failed_provider: string | null
}

export interface ProviderStatus {
  name: string
  available: boolean
  model: string
}

export interface HealthResponse {
  status: string
  version: string
  providers: ProviderStatus[]
}

export async function sendMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await window.fetch(
    `${JARVIS_ENGINE_URL}/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }
  )
  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`)
  }
  return response.json()
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/health`)
  if (!response.ok) {
    throw new Error("Health check failed")
  }
  return response.json()
}

export async function getConversation(
  conversationId: string
): Promise<any[]> {
  const response = await window.fetch(
    `${JARVIS_ENGINE_URL}/conversation/${conversationId}`
  )
  if (!response.ok) {
    throw new Error("Failed to get conversation")
  }
  return response.json()
}

export async function getConversations(): Promise<any[]> {
  const response = await window.fetch(
    `${JARVIS_ENGINE_URL}/conversations`
  )
  if (!response.ok) {
    throw new Error("Failed to get conversations")
  }
  return response.json()
}

export async function deletePluginCredentials(pluginId: string): Promise<void> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/${pluginId}/credentials`, {
    method: "DELETE"
  })
  if (!response.ok) throw new Error("Failed to delete credentials")
}

export async function getGoogleAuthUrl(): Promise<string> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/google/auth-url`)
  if (!response.ok) throw new Error("Failed to get auth URL")
  const data = await response.json()
  return data.url
}

export async function checkGmail(): Promise<any[]> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/gmail/unread`)
  if (!response.ok) throw new Error("Failed to check Gmail")
  return response.json()
}

export async function searchGmail(query: string): Promise<any[]> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/gmail/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  })
  if (!response.ok) throw new Error("Failed to search Gmail")
  return response.json()
}

export async function sendEmail(to: string, subject: string, body: string): Promise<void> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/gmail/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to, subject, body })
  })
  if (!response.ok) throw new Error("Failed to send email")
}

export async function checkCalendar(): Promise<any[]> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/calendar/today`)
  if (!response.ok) throw new Error("Failed to check calendar")
  return response.json()
}

export async function checkUpcomingEvents(): Promise<any[]> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/calendar/upcoming`)
  if (!response.ok) throw new Error("Failed to check upcoming events")
  return response.json()
}

export async function createEvent(title: string, start: string, end: string): Promise<void> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/plugins/calendar/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, start, end, description: "" })
  })
  if (!response.ok) throw new Error("Failed to create event")
}

export async function deleteConversation(conversationId: string, pin: string): Promise<void> {
  const response = await window.fetch(
    `${JARVIS_ENGINE_URL}/conversation/${conversationId}?pin=${encodeURIComponent(pin)}`,
    { method: "DELETE" }
  )
  if (!response.ok) {
    throw new Error("Failed to delete conversation")
  }
}

export async function updateConversationTitle(conversationId: string, title: string): Promise<void> {
  const response = await window.fetch(
    `${JARVIS_ENGINE_URL}/conversation/${conversationId}/title`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    }
  )
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to update conversation title");
  }
}

export async function sendMessageStream(
  request: ChatRequest,
  onMeta: (meta: { conversationId: string, searchPerformed: boolean, searchQuery: string, sources: SearchSource[] }) => void,
  onSearchStarted: (query: string) => void,
  onSearchComplete: (sources: SearchSource[]) => void,
  onToken: (token: string) => void,
  onDone: (
    conversationId: string,
    fullResponse: string,
    sources: SearchSource[],
    providerUsed: string,
    modelUsed: string,
    fallbackOccurred: boolean,
    failedProvider: string | null
  ) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await window.fetch(
      `${JARVIS_ENGINE_URL}/chat/stream`,
      {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify(request),
      }
    )
    
    if (!response.ok || !response.body) {
      throw new Error(
        `Stream failed: ${response.status}`
      )
    }
    
    const reader = response.body.getReader()
    const decoder = new window.TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split("\n").filter(Boolean)
      
      for (const line of lines) {
        try {
          const data = JSON.parse(line)
          if (data.type === "meta") {
            onMeta({
              conversationId: data.conversation_id || "",
              searchPerformed: data.search_performed || false,
              searchQuery: data.search_query || "",
              sources: data.sources || []
            })
          } else if (data.type === "search_started") {
            if (onSearchStarted) {
              onSearchStarted(data.query || "")
            }
          } else if (data.type === "search_complete") {
            if (onSearchComplete) {
              onSearchComplete(
                Array.isArray(data.sources) ? data.sources : []
              )
            }
          } else if (data.type === "search_timeout") {
            console.log("Search timed out, AI answering from training")
          } else if (data.type === "token") {
            onToken(data.content)
          } else if (data.type === "done") {
            onDone(
              data.conversation_id || "",
              data.full_response || "",
              Array.isArray(data.sources) ? data.sources : [],
              data.provider_used || "unknown",
              data.model_used || "unknown",
              !!data.fallback_occurred,
              data.failed_provider || null
            )
          }
        } catch {
          // Skip malformed lines
        }
      }
    }
  } catch (error) {
    onError(
      error instanceof Error 
        ? error.message 
        : "Stream error"
    )
  }
}

export async function getMemories(): Promise<any[]> {
  try {
    const response = await window.fetch(`${JARVIS_ENGINE_URL}/memories`)
    if (!response.ok) return []
    const memories = await response.json()
    return Array.isArray(memories) ? memories : []
  } catch {
    return []
  }
}

export async function getMemoryCount(): Promise<number> {
  try {
    const response = await window.fetch(`${JARVIS_ENGINE_URL}/memories`)
    if (!response.ok) return 0
    const memories = await response.json()
    return Array.isArray(memories) ? memories.length : 0
  } catch {
    return 0
  }
}

export interface MemoryItem {
  id: string;
  content: string;
  category: string;
  importance: number;
  created_at: string;
  last_accessed: string;
  access_count: number;
  source_conversation_id: string | null;
}

export async function updateMemory(
  memoryId: string,
  updates: { content?: string; category?: string; importance?: number }
): Promise<MemoryItem> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/memories/${memoryId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  })
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || "Failed to update memory")
  }
  return response.json()
}

export async function deleteMemory(memoryId: string, pin: string): Promise<void> {
  const response = await window.fetch(
    `${JARVIS_ENGINE_URL}/memories/${memoryId}?pin=${encodeURIComponent(pin)}`,
    { method: "DELETE" }
  )
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || "Failed to delete memory")
  }
}

export async function switchProvider(provider: string, model: string): Promise<void> {
  await window.fetch(
    `${JARVIS_ENGINE_URL}/provider/switch`,
    {
      method: "POST",
      headers: { 
        "Content-Type": "application/json" 
      },
      body: JSON.stringify({ provider, model }),
    }
  )
}

export async function setOpenRouterKey(
  apiKey: string
): Promise<void> {
  try {
    await window.fetch(
      `${JARVIS_ENGINE_URL}/config/openrouter-key`,
      {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ api_key: apiKey }),
      }
    )
  } catch {
    console.error("Failed to set OpenRouter key")
  }
}

export async function setGroqKey(
  apiKey: string
): Promise<void> {
  try {
    await window.fetch(
      `${JARVIS_ENGINE_URL}/config/groq-key`,
      {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ api_key: apiKey }),
      }
    )
  } catch {
    console.error("Failed to set Groq key")
  }
}

export async function setGeminiKey(
  apiKey: string
): Promise<void> {
  try {
    await window.fetch(
      `${JARVIS_ENGINE_URL}/config/gemini-key`,
      {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ api_key: apiKey }),
      }
    )
  } catch {
    console.error("Failed to set Gemini key")
  }
}

export async function startVoice(): Promise<void> {
  await window.fetch(
    `${JARVIS_ENGINE_URL}/voice/start`,
    { method: "POST" }
  )
}

export async function stopVoice(): Promise<void> {
  await window.fetch(
    `${JARVIS_ENGINE_URL}/voice/stop`,
    { method: "POST" }
  )
}

export async function getVoiceStatus(): Promise<any> {
  const r = await window.fetch(
    `${JARVIS_ENGINE_URL}/voice/status`
  )
  return r.json()
}

let voiceSocket: WebSocket | null = null
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
let isExplicitlyClosed = false

export function disconnectVoiceWebSocket(): void {
  isExplicitlyClosed = true
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  if (voiceSocket) {
    if (voiceSocket.readyState === WebSocket.OPEN || voiceSocket.readyState === WebSocket.CONNECTING) {
      voiceSocket.close()
    }
    voiceSocket = null
  }
}

export interface VoiceResponseMeta {
  providerUsed: string | null
  modelUsed: string | null
  fallbackOccurred: boolean
  failedProvider: string | null
}

export function connectVoiceWebSocket(
  onVoiceInput: (text: string, seq?: number) => void,
  onVoiceResponse: (text: string, seq?: number, meta?: VoiceResponseMeta) => void,
  onVoiceStatus: (status: string, seq?: number) => void,
  onAudioLevel?: (level: number) => void
): () => void {
  // Clear any pending reconnect
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }

  isExplicitlyClosed = false

  // If already open or connecting, return cleanup without creating a duplicate socket
  if (voiceSocket && (voiceSocket.readyState === WebSocket.OPEN || voiceSocket.readyState === WebSocket.CONNECTING)) {
    console.log("[WS] Voice WebSocket already connected/connecting, skipping redundant connection")
    return () => {
      disconnectVoiceWebSocket()
    }
  }

  // If socket is in CLOSING state, clear it
  if (voiceSocket) {
    try {
      voiceSocket.close()
    } catch {}
    voiceSocket = null
  }

  console.log("[WS] Connecting to Voice WebSocket...")
  const ws = new WebSocket("ws://localhost:8765/ws/voice")
  voiceSocket = ws

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      const seq = typeof data.seq === "number" ? data.seq : undefined
      if (data.type === "voice_input") {
        onVoiceInput(data.text, seq)
      } else if (data.type === "voice_response") {
        onVoiceResponse(data.text, seq, {
          providerUsed: data.provider_used ?? null,
          modelUsed: data.model_used ?? null,
          fallbackOccurred: !!data.fallback_occurred,
          failedProvider: data.failed_provider ?? null
        })
      } else if (data.type === "voice_status") {
        onVoiceStatus(data.status, seq)
      } else if (data.type === "audio_level") {
        onAudioLevel?.(data.level)
      }
    } catch (err) {
      console.error("[WS] Error parsing WebSocket message:", err)
    }
  }

  ws.onclose = () => {
    if (isExplicitlyClosed) {
      console.log("[WS] Voice WebSocket explicitly closed, not reconnecting")
      return
    }
    console.log("[WS] Voice WebSocket closed, attempting reconnect in 2s...")
    reconnectTimeout = setTimeout(() => {
      if (!isExplicitlyClosed && (!voiceSocket || voiceSocket.readyState === WebSocket.CLOSED)) {
        connectVoiceWebSocket(
          onVoiceInput, onVoiceResponse, onVoiceStatus, onAudioLevel
        )
      }
    }, 2000)
  }

  ws.onerror = (err) => {
    console.error("[WS] Voice WebSocket error:", err)
  }

  return () => {
    disconnectVoiceWebSocket()
  }
}

export interface JarvisSettings {
  personality_mode: string
  modifier: string
  address_preference: string
  daily_briefing_enabled: boolean
  last_briefing_date: string
  provider_override: string | null
  fallback_mode: "auto" | "ask"
}

export async function getSettings(): Promise<JarvisSettings> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/settings`)
  if (!response.ok) {
    throw new Error("Failed to fetch settings")
  }
  return response.json()
}

export async function updateSettings(
  settings: { personality_mode?: string; modifier?: string; conversation_delete_pin?: string; address_preference?: string; daily_briefing_enabled?: boolean; last_briefing_date?: string; provider_override?: string | null; fallback_mode?: string }
): Promise<JarvisSettings> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings)
  })
  if (!response.ok) {
    throw new Error("Failed to update settings")
  }
  return response.json()
}

export async function verifyDeletePin(pin: string): Promise<boolean> {
  const response = await window.fetch(`${JARVIS_ENGINE_URL}/settings/verify-pin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pin })
  })
  if (!response.ok) {
    throw new Error("Failed to verify PIN")
  }
  const data = await response.json()
  return !!data.valid
}

