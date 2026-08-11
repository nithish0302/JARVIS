from pydantic import BaseModel
from typing import Literal

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    provider: str = "ollama"
    model: str = "llama3.2:3b"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    provider_used: str
    model_used: str
    search_query: str | None = None

class ProviderStatus(BaseModel):
    name: str
    available: bool
    model: str

class HealthResponse(BaseModel):
    status: str
    version: str
    providers: list[ProviderStatus]

class Memory(BaseModel):
    id: str
    content: str
    category: str = "general"
    importance: int = 5
    created_at: str
    last_accessed: str
    access_count: int = 0
    source_conversation_id: str | None = None

class CreateMemoryRequest(BaseModel):
    content: str
    category: str = "general"
    importance: int = 5

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    formatted: str
