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

export async function sendMessageStream(
  request: ChatRequest,
  onMeta: (meta: { conversationId: string, searchPerformed: boolean, searchQuery: string, sources: SearchSource[] }) => void,
  onToken: (token: string) => void,
  onDone: (
    conversationId: string, 
    fullResponse: string,
    sources: SearchSource[]
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
          } else if (data.type === "token") {
            onToken(data.content)
          } else if (data.type === "done") {
            onDone(
              data.conversation_id || "",
              data.full_response || "",
              Array.isArray(data.sources) ? data.sources : []
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
