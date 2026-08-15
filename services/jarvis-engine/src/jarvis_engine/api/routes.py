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
from ..tools.web_search import (
  search_web, format_search_results
)
from ..tools.search_detector import (
  needs_web_search, extract_search_query
)

router = APIRouter()

@router.post("/search")
async def search_endpoint(request: dict):
  query = request.get("query", "")
  if not query:
    raise HTTPException(
      status_code=400,
      detail="Query is required"
    )
  
  results = await search_web(query)
  formatted = format_search_results(results, query)
  
  return {
    "query": query,
    "results": results,
    "formatted": formatted
  }

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

UI_ACTION_INSTRUCTION = """
You can control the JARVIS interface by including
special action tags in your response.

Available UI actions:
[UI_ACTION:chat_mode_on] - Switch to full chat mode
[UI_ACTION:chat_mode_off] - Switch back to graph mode
[UI_ACTION:graph_expand] - Expand graph to Level 1
[UI_ACTION:graph_collapse] - Collapse graph to Level 0
[UI_ACTION:graph_open_hub:Skills] - Open Skills hub
[UI_ACTION:graph_open_hub:Tools] - Open Tools hub
[UI_ACTION:graph_open_hub:Files] - Open Files hub
[UI_ACTION:graph_open_hub:Notes] - Open Notes hub
[UI_ACTION:graph_open_hub:Models] - Open Models hub
[UI_ACTION:graph_open_hub:Conversations] - Open Conversations
[UI_ACTION:conversations_open] - Open conversation panel
[UI_ACTION:conversations_close] - Close conversation panel

Rules:
- Only use actions when user explicitly requests them
- Put action tags at the END of your response
- Never show the raw tag text to the user
- Multiple actions can be included if needed
- Example: "Opening skills now. [UI_ACTION:graph_open_hub:Skills]"
"""

JARVIS_SYSTEM_PROMPT += "\n" + UI_ACTION_INSTRUCTION

SEARCH_STRICT_INSTRUCTION = """
When web search results are provided:
- Use ONLY information from the search results
- Do NOT add facts from your training data
- Do NOT invent statistics, numbers, or dates
- If the search results don't contain specific
  data (like subscriber counts), say:
  "I found [X] but couldn't confirm [Y]"
- Always be honest about uncertainty
- Cite which source the information came from
"""

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
    search_performed = False
    search_query_used = ""
    search_sources = []
    search_context = ""
    
    if needs_web_search(request.message):
        search_query_used = extract_search_query(request.message)
        search_results = await search_web(search_query_used, max_results=4)
        if search_results:
            search_performed = True
            search_sources = search_results
            search_context = f"\n\nReal-time web search results for '{search_query_used}':\n"
            for i, r in enumerate(search_results, 1):
                search_context += f"\n{i}. {r['title']}\n   {r['snippet']}\n   Source: {r['url']}\n"
            search_context += "\nUse these results to answer accurately. Always cite your sources."
            search_context += SEARCH_STRICT_INSTRUCTION
            
    system_message = Message(
        role="system",
        content=JARVIS_SYSTEM_PROMPT + memory_context + search_context,
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
        model_used=model_used,
        search_performed=search_performed,
        search_query=search_query_used,
        sources=search_sources
    )

@router.post("/chat/stream")
async def chat_stream_endpoint(
  request: ChatRequest
):
  try:
    print(f"Stream request: {request.message[:50]}")
    conversation_id = (
      request.conversation_id or str(uuid.uuid4())
    )
    
    # Get relevant memories
    relevant_memories = await memory_manager.get_relevant_memories(request.message, limit=5)
    memory_context = ""
    if relevant_memories:
        memory_lines = [f"- {m['content']}" for m in relevant_memories]
        memory_context = "\n\nRelevant memories about Nithish:\n" + "\n".join(memory_lines)

    search_performed = False
    search_query_used = ""
    search_sources = []
    search_context = ""
    
    if needs_web_search(request.message):
        search_query_used = extract_search_query(request.message)
        search_results = await search_web(search_query_used, max_results=4)
        if search_results:
            search_performed = True
            search_sources = search_results
            search_context = f"\n\nReal-time web search results for '{search_query_used}':\n"
            for i, r in enumerate(search_results, 1):
                search_context += f"\n{i}. {r['title']}\n   {r['snippet']}\n   Source: {r['url']}\n"
            search_context += "\nUse these results to answer accurately. Always cite your sources."
            search_context += SEARCH_STRICT_INSTRUCTION

    system_message = Message(
      role="system",
      content=JARVIS_SYSTEM_PROMPT + memory_context + search_context,
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
    
    async def generate():
      try:
        # Send meta chunk first
        try:
          yield json_module.dumps({
            "type": "meta",
            "conversation_id": conversation_id,
            "search_performed": search_performed,
            "search_query": search_query_used,
            "sources": [
              {
                "title": str(s.get("title", "")),
                "url": str(s.get("url", "")),
                "snippet": str(s.get("snippet", "")[:200]),
                "source": str(s.get("source", ""))
              }
              for s in (search_sources or [])
            ]
          }) + "\n"
        except Exception as meta_err:
          print(f"Meta chunk error: {meta_err}")
          yield json_module.dumps({
            "type": "meta",
            "conversation_id": conversation_id,
            "search_performed": False,
            "search_query": "",
            "sources": []
          }) + "\n"

        # Stream tokens from Ollama
        full_response_parts = []
        try:
          async for token in (
            provider_manager.providers[0].stream(
              full_messages
            )
          ):
            full_response_parts.append(token)
            yield json_module.dumps({
              "type": "token",
              "content": token
            }) + "\n"
        except Exception as stream_err:
          print(f"Stream token error: {stream_err}")
          # If streaming fails midway, yield what we have

        # Save complete response
        complete_response = "".join(full_response_parts)
        
        if complete_response:
          try:
            await save_message(
              conversation_id=conversation_id,
              role="assistant",
              content=complete_response,
              provider_used="ollama",
              model_used=provider_manager.providers[0].model
            )
          except Exception as save_err:
            print(f"Save message error: {save_err}")

          # Extract memories (non-blocking)
          try:
            await memory_manager.extract_and_save_memories(
              request.message,
              conversation_id
            )
          except Exception as mem_err:
            print(f"Memory extraction error: {mem_err}")

        # Send done chunk
        yield json_module.dumps({
          "type": "done",
          "conversation_id": conversation_id,
          "full_response": complete_response
        }) + "\n"

      except Exception as fatal_err:
        print(f"FATAL stream error: {fatal_err}")
        import traceback
        traceback.print_exc()
        try:
          yield json_module.dumps({
            "type": "error",
            "message": str(fatal_err)
          }) + "\n"
        except:
          pass
    
    return StreamingResponse(
      generate(),
      media_type="application/x-ndjson"
    )
  except Exception as setup_err:
    print(f"Stream setup error: {setup_err}")
    import traceback
    traceback.print_exc()
    raise

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

@router.post("/memories/deduplicate")
async def deduplicate_memories():
  async with aiosqlite.connect(
    settings.DB_PATH
  ) as db:
    # Keep only the oldest memory per 
    # content prefix, delete duplicates
    await db.execute("""
      DELETE FROM memories 
      WHERE id NOT IN (
        SELECT MIN(id) 
        FROM memories 
        GROUP BY LOWER(SUBSTR(content, 1, 100))
      )
    """)
    await db.commit()
    
    cursor = await db.execute(
      "SELECT COUNT(*) FROM memories"
    )
    count = await cursor.fetchone()
    return {
      "status": "deduplicated",
      "memories_remaining": count[0]
    }

@router.post("/config/openrouter-key")
async def set_openrouter_key(
  request: dict
):
  key = request.get("api_key", "")
  # Store in environment for this session
  import os
  os.environ["OPENROUTER_API_KEY"] = key
  # Reload settings
  from ..core.config import settings
  settings.OPENROUTER_API_KEY = key
  return {"status": "updated"}
