import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json as json_module
from typing import List

from ..core.models import ChatRequest, ChatResponse, HealthResponse, Message, Memory, CreateMemoryRequest
from ..core.config import settings
from ..providers.manager import provider_manager
from ..memory.conversation import save_message, get_conversation_messages, delete_conversation, get_conversations
from ..memory.memory_manager import memory_manager

router = APIRouter()

JARVIS_SYSTEM_PROMPT = """You are JARVIS, a premium 
AI desktop assistant for Nithish. You are intelligent,
efficient, and highly capable.

Personality:
- Direct and confident, never vague or wishy-washy
- Professional but warm
- Concise — say what needs to be said, nothing more
- Occasionally address Nithish as "sir" when natural,
  not every sentence
- Never start responses with "Certainly!", 
  "Of course!", "Great!", or similar filler phrases
- When you do not know something, say so directly
- Reference earlier parts of the conversation 
  naturally when relevant

You are not a generic chatbot. You are JARVIS — 
act like it."""

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    conversation_id_exists = request.conversation_id is not None
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Get relevant memories
    relevant_memories = await memory_manager.get_relevant_memories(request.message, limit=5)
    memory_context = ""
    if relevant_memories:
        memory_lines = [f"- {m['content']}" for m in relevant_memories]
        memory_context = "\n\nRelevant memories about Nithish:\n" + "\n".join(memory_lines)
    
    # Create system message
    system_message = Message(
        role="system",
        content=JARVIS_SYSTEM_PROMPT + memory_context,
        timestamp=""
    )
    
    # Load existing conversation history
    history = []
    if conversation_id_exists:
        history = await get_conversation_messages(conversation_id)
        
    # Create new user message
    new_user_message = Message(
        role="user",
        content=request.message,
        timestamp=""
    )
    
    # Build full message list
    full_messages = [system_message] + history + [new_user_message]
    
    # Save user message to DB
    await save_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    
    # Get AI response
    response_text, provider_used, model_used = await provider_manager.chat(full_messages)
    
    # Save assistant message to DB
    await save_message(
        conversation_id=conversation_id,
        role="assistant",
        content=response_text,
        provider_used=provider_used,
        model_used=model_used
    )
    
    # Extract and save memories from user message
    await memory_manager.extract_and_save_memories(
        request.message,
        conversation_id
    )
    
    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        provider_used=provider_used,
        model_used=model_used
    )

@router.post("/chat/stream")
async def chat_stream_endpoint(
  request: ChatRequest
):
  conversation_id = (
    request.conversation_id or str(uuid.uuid4())
  )
  
  # Get relevant memories
  relevant_memories = await memory_manager.get_relevant_memories(request.message, limit=5)
  memory_context = ""
  if relevant_memories:
      memory_lines = [f"- {m['content']}" for m in relevant_memories]
      memory_context = "\n\nRelevant memories about Nithish:\n" + "\n".join(memory_lines)

  system_message = Message(
    role="system",
    content=JARVIS_SYSTEM_PROMPT + memory_context,
    timestamp=""
  )
  
  history = []
  if request.conversation_id:
    history = await get_conversation_messages(
      conversation_id
    )
  
  new_user_message = Message(
    role="user",
    content=request.message,
    timestamp=""
  )
  
  full_messages = (
    [system_message] + history + [new_user_message]
  )
  
  await save_message(
    conversation_id=conversation_id,
    role="user",
    content=request.message
  )
  
  full_response = []
  
  async def generate():
    nonlocal full_response
    
    # Send conversation_id first as metadata
    yield json_module.dumps({
      "type": "meta",
      "conversation_id": conversation_id
    }) + "\n"
    
    # Stream tokens from Ollama
    async for token in (
      provider_manager.providers[0].stream(
        full_messages
      )
    ):
      full_response.append(token)
      yield json_module.dumps({
        "type": "token",
        "content": token
      }) + "\n"
    
    # Send done signal
    complete_response = "".join(full_response)
    await save_message(
      conversation_id=conversation_id,
      role="assistant",
      content=complete_response,
      provider_used="ollama",
      model_used=provider_manager.providers[0].model
    )
    
    # Extract and save memories from user message
    await memory_manager.extract_and_save_memories(
        request.message,
        conversation_id
    )
    yield json_module.dumps({
      "type": "done",
      "full_response": complete_response
    }) + "\n"
  
  return StreamingResponse(
    generate(),
    media_type="application/x-ndjson"
  )

@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    statuses = await provider_manager.get_status()
    return HealthResponse(
        status="online",
        version=settings.VERSION,
        providers=statuses
    )

@router.get("/conversation/{conversation_id}", response_model=List[Message])
async def get_conversation_endpoint(conversation_id: str):
    messages = await get_conversation_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return messages

@router.delete("/conversation/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    await delete_conversation(conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}

@router.get("/providers")
async def get_providers_endpoint():
    return await provider_manager.get_status()

class SwitchProviderRequest(BaseModel):
    provider: str
    model: str

@router.post("/provider/switch")
async def switch_provider_endpoint(request: SwitchProviderRequest):
    provider_manager.set_active_provider(request.provider, request.model)
    return {"status": "success", "provider": request.provider, "model": request.model}

@router.get("/memories", response_model=List[Memory])
async def get_memories_endpoint():
    memories = await memory_manager.get_all_memories(limit=50)
    return memories

@router.post("/memories", response_model=Memory)
async def create_memory_endpoint(request: CreateMemoryRequest):
    memory_id = await memory_manager.save_memory(
        content=request.content,
        category=request.category,
        importance=request.importance
    )
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    return Memory(
        id=memory_id,
        content=request.content,
        category=request.category,
        importance=request.importance,
        created_at=now,
        last_accessed=now,
        access_count=0,
        source_conversation_id=None
    )

@router.delete("/memories/{memory_id}")
async def delete_memory_endpoint(memory_id: str):
    deleted = await memory_manager.delete_memory(memory_id)
    return {"deleted": deleted}

@router.get("/memories/search", response_model=List[Memory])
async def search_memories_endpoint(q: str):
    results = await memory_manager.get_relevant_memories(q, limit=50)
    return results

@router.get("/conversations")
async def get_conversations_endpoint():
    return await get_conversations(limit=10)
