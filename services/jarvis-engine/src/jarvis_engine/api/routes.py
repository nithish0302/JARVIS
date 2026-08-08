import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from ..core.models import ChatRequest, ChatResponse, HealthResponse, Message
from ..core.config import settings
from ..providers.manager import provider_manager
from ..memory.conversation import save_message, get_conversation_messages, delete_conversation

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
    
    # Create system message
    system_message = Message(
        role="system",
        content=JARVIS_SYSTEM_PROMPT,
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
    
    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        provider_used=provider_used,
        model_used=model_used
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
