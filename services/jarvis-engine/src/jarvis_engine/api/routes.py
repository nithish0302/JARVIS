import uuid
import asyncio
import time
from fastapi import APIRouter, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json as json_module
from typing import List, Set
import aiosqlite

from ..core.models import ChatRequest, ChatResponse, HealthResponse, Message, Memory, CreateMemoryRequest, UpdateMemoryRequest
from ..core.config import settings
from ..core.database import get_setting, set_setting
from ..providers.manager import provider_manager
from ..memory.conversation import save_message, get_conversation_messages, delete_conversation, get_conversations, update_conversation_title
from ..memory.memory_manager import memory_manager
from ..tools.web_search import (
  search_web, format_search_results
)
from ..tools.search_detector import (
  needs_web_search, extract_search_query
)
from ..voice.voice_manager import voice_manager
from ..core.utils import safe_print
from ..providers import fallback as fallback_module
from ..providers.fallback import run_cascade, build_fallback_note, build_ask_message, build_override_unavailable_message, build_unconfigured_message

router = APIRouter()

# WebSocket connections for voice events
connected_clients: Set[WebSocket] = set()
_voice_event_seq = 0
_voice_seq_lock = asyncio.Lock()

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

@router.post("/voice/start")
async def start_voice():
  # Use the SAME shared handler the startup path registers. This used to
  # install a 1-argument M2-era stub, which clobbered the real handler and
  # made every transcription fail with "takes 1 positional argument but 2
  # were given".
  from ..voice.transcription_handler import handle_transcription

  voice_manager.initialize(handle_transcription)
  return {"status": "voice_started"}

@router.post("/voice/stop")
async def stop_voice():
  voice_manager.shutdown()
  return {"status": "voice_stopped"}

@router.get("/voice/status")
async def voice_status():
  return {
    "is_listening": voice_manager.is_listening,
    "wake_word_model": "wake_up_jarvis",
    "status": "active" if
      voice_manager.wake_word_detector
      else "inactive"
  }

@router.post("/tts/stop")
async def stop_tts():
  from ..voice.tts_engine import tts_engine
  tts_engine.stop()
  return {"status": "stopped"}

@router.get("/tts/status")
async def tts_status():
  from ..voice.tts_engine import tts_engine
  return {
    "is_speaking": tts_engine.is_speaking,
    "voice": tts_engine.voice
  }

@router.get("/settings")
async def get_settings_endpoint():
    personality_mode = await get_setting("personality_mode", settings.PERSONALITY_MODE)
    modifier = await get_setting("modifier", settings.MODIFIER)
    address_preference = await get_setting("address_preference", settings.ADDRESS_PREFERENCE)
    daily_briefing_enabled = await get_setting(
        "daily_briefing_enabled", settings.DAILY_BRIEFING_ENABLED
    ) == "true"
    last_briefing_date = await get_setting(
        "last_briefing_date", settings.LAST_BRIEFING_DATE
    )
    provider_override = await get_setting(
        "provider_override", settings.PROVIDER_OVERRIDE
    )
    fallback_mode = await get_setting("fallback_mode", settings.FALLBACK_MODE)
    preferred_provider = await get_setting(
        "preferred_provider", settings.PREFERRED_PROVIDER
    )
    preferred_model = await get_setting(
        "preferred_model", settings.PREFERRED_MODEL
    )
    # These four reflect a LIVE SETTINGS-TABLE OVERRIDE specifically (not
    # whether the provider works at all) - ProvidersSection.tsx uses them
    # to show "Active Override" next to a field whose value came from a
    # manual Settings entry rather than .env. A provider configured only
    # via .env (never overridden through Settings) correctly reads false
    # here.
    gemini_configured = await get_setting("GEMINI_API_KEY") != ""
    groq_configured = await get_setting("GROQ_API_KEY") != ""
    openrouter_configured = await get_setting("OPENROUTER_API_KEY") != ""
    ollama_configured = await get_setting("OLLAMA_HOST") != ""

    return {
        "personality_mode": personality_mode,
        "modifier": modifier,
        "address_preference": address_preference,
        "daily_briefing_enabled": daily_briefing_enabled,
        "last_briefing_date": last_briefing_date,
        "provider_override": provider_override or None,
        "fallback_mode": fallback_mode,
        # Read-only here - written by /provider/switch, not by this
        # endpoint. Soft first-choice preference, distinct from
        # provider_override's hard lock (see PREFERRED_PROVIDER in
        # core/config.py).
        "preferred_provider": preferred_provider or None,
        "preferred_model": preferred_model or None,
        "gemini_configured": gemini_configured,
        "groq_configured": groq_configured,
        "openrouter_configured": openrouter_configured,
        "ollama_configured": ollama_configured,
        # True if ANY provider has a working credential/host from EITHER
        # source (.env default or a settings-table override) - unlike the
        # four flags above, this is what "first run, nothing set up yet"
        # actually means. See ProviderManager.is_unconfigured().
        "any_provider_configured": not provider_manager.is_unconfigured(),
    }

@router.post("/settings/verify-pin")
async def verify_delete_pin_endpoint(request: dict):
    pin = str(request.get("pin", "")).strip()
    stored_pin = await get_setting("conversation_delete_pin", settings.CONVERSATION_DELETE_PIN)
    return {"valid": pin == stored_pin}

@router.post("/settings")
async def update_settings_endpoint(request: dict):
    if "personality_mode" in request:
        mode = str(request["personality_mode"]).lower().strip()
        if mode in ("assistant", "developer", "research"):
            await set_setting("personality_mode", mode)
    if "modifier" in request:
        mod = str(request["modifier"]).lower().strip()
        if mod in ("none", "planner", "quiet"):
            await set_setting("modifier", mod)
    if "conversation_delete_pin" in request:
        pin = str(request["conversation_delete_pin"]).strip()
        if pin.isdigit() and len(pin) == 4:
            await set_setting("conversation_delete_pin", pin)
    if "address_preference" in request:
        addr = str(request["address_preference"]).strip()
        # Any short string (a name, "boss", etc.) or "" for no address
        # term at all - just cap the length, no other restriction.
        if len(addr) <= 20:
            await set_setting("address_preference", addr)
    if "daily_briefing_enabled" in request:
        await set_setting(
            "daily_briefing_enabled",
            "true" if request["daily_briefing_enabled"] else "false"
        )
    if "last_briefing_date" in request:
        # Mainly a testing/reset affordance - "" forces the next
        # interaction to re-trigger a briefing, otherwise must be a real
        # YYYY-MM-DD date.
        raw = str(request["last_briefing_date"]).strip()
        if raw == "":
            await set_setting("last_briefing_date", "")
        else:
            from datetime import datetime
            try:
                datetime.strptime(raw, "%Y-%m-%d")
                await set_setting("last_briefing_date", raw)
            except ValueError:
                pass
    if "provider_override" in request:
        raw_override = request["provider_override"]
        override = "" if raw_override is None else str(raw_override).strip().lower()
        if override in ("none", "null"):
            override = ""
        if override == "" or override in fallback_module.VALID_PROVIDERS:
            await set_setting("provider_override", override)
    if "fallback_mode" in request:
        mode = str(request["fallback_mode"]).strip().lower()
        if mode in ("auto", "ask"):
            await set_setting("fallback_mode", mode)
            if mode == "auto":
                # Switching back to auto clears any pending "which provider
                # would you like?" state - it no longer applies.
                await set_setting("awaiting_provider_choice", "false")

    personality_mode = await get_setting("personality_mode", settings.PERSONALITY_MODE)
    modifier = await get_setting("modifier", settings.MODIFIER)
    address_preference = await get_setting("address_preference", settings.ADDRESS_PREFERENCE)
    daily_briefing_enabled = await get_setting(
        "daily_briefing_enabled", settings.DAILY_BRIEFING_ENABLED
    ) == "true"
    last_briefing_date = await get_setting(
        "last_briefing_date", settings.LAST_BRIEFING_DATE
    )
    provider_override = await get_setting(
        "provider_override", settings.PROVIDER_OVERRIDE
    )
    fallback_mode = await get_setting("fallback_mode", settings.FALLBACK_MODE)
    preferred_provider = await get_setting(
        "preferred_provider", settings.PREFERRED_PROVIDER
    )
    preferred_model = await get_setting(
        "preferred_model", settings.PREFERRED_MODEL
    )
    gemini_configured = await get_setting("GEMINI_API_KEY") != ""
    groq_configured = await get_setting("GROQ_API_KEY") != ""
    openrouter_configured = await get_setting("OPENROUTER_API_KEY") != ""
    ollama_configured = await get_setting("OLLAMA_HOST") != ""

    return {
        "personality_mode": personality_mode,
        "modifier": modifier,
        "address_preference": address_preference,
        "daily_briefing_enabled": daily_briefing_enabled,
        "last_briefing_date": last_briefing_date,
        "provider_override": provider_override or None,
        "fallback_mode": fallback_mode,
        "preferred_provider": preferred_provider or None,
        "preferred_model": preferred_model or None,
        "gemini_configured": gemini_configured,
        "groq_configured": groq_configured,
        "openrouter_configured": openrouter_configured,
        "ollama_configured": ollama_configured,
        "any_provider_configured": not provider_manager.is_unconfigured(),
    }

@router.put("/settings/provider-config")
async def update_provider_config(request: dict):
    if "gemini_api_key" in request:
        val = str(request["gemini_api_key"]).strip()
        await set_setting("GEMINI_API_KEY", val)
        settings.GEMINI_API_KEY = val
    if "groq_api_key" in request:
        val = str(request["groq_api_key"]).strip()
        await set_setting("GROQ_API_KEY", val)
        settings.GROQ_API_KEY = val
    if "openrouter_api_key" in request:
        val = str(request["openrouter_api_key"]).strip()
        await set_setting("OPENROUTER_API_KEY", val)
        settings.OPENROUTER_API_KEY = val
    if "ollama_host" in request:
        val = str(request["ollama_host"]).strip()
        await set_setting("OLLAMA_HOST", val)
        settings.OLLAMA_HOST = val
    return {"status": "ok"}

@router.post("/voice/status/update")
async def update_voice_status(request: dict):
  status = request.get("status", "idle")
  await broadcast_voice_event({
    "type": "voice_status",
    "status": status
  })
  return {"status": status}

@router.post("/voice/input")
async def voice_input_endpoint(request: dict):
  text = request.get("text", "").strip()
  direct_response = request.get("direct_response")

  print(f"[VOICE INPUT ENDPOINT] Received: {text}")
  if not text:
    raise HTTPException(
      status_code=400,
      detail="No text provided"
    )

  # Broadcast processing status
  await broadcast_voice_event({
    "type": "voice_status",
    "status": "processing"
  })

  # Daily briefing check - computed once here so it applies uniformly
  # whether the first interaction of the day is a direct pattern-matched
  # command (below) or goes through the LLM (further down).
  briefing_address_preference = await get_setting(
    "address_preference", settings.ADDRESS_PREFERENCE
  )
  briefing_prefix = await maybe_build_daily_briefing(briefing_address_preference)

  # Handle direct command - already executed, broadcast (TTS happens in main.py)
  if direct_response:
    direct_response = briefing_prefix + direct_response
    print(f"[VOICE] Direct command executed: {direct_response}")
    await broadcast_voice_event({
      "type": "voice_input",
      "text": text
    })
    await broadcast_voice_event({
      "type": "voice_response",
      "text": direct_response
    })
    # Note: TTS status (speaking->idle) is handled in main.py callback
    return {
      "response": direct_response,
      "conversation_id": "",
      "provider_used": "direct",
      "model_used": "direct"
    }

  import os

  # Run automation detection first
  automation_results = []
  if needs_automation(text) and settings.GROQ_API_KEY:
    automation_results = await generate_automation_command(
      text, settings.GROQ_API_KEY
    )
    automation_results = deduplicate_actions(
      automation_results
    )
    automation_results = remove_duplicate_apps(
      automation_results
    )

  # Check file system commands
  is_file_cmd, file_action = is_file_system_command(text)

  # Build automation context
  automation_context = ""

  if is_file_cmd:
    action = file_action["action"]
    path = file_action.get("path", "")
    requires_confirm = file_action.get(
      "requires_confirmation", False
    )
    if requires_confirm:
      automation_context = (
        f"[FILE SYSTEM COMMAND DETECTED]\n"
        f"You MUST include: "
        f"[UI_ACTION:confirm_action:{action}:{path}]\n"
        f"Ask confirmation naturally."
      )
    else:
      automation_context = (
        f"[FILE SYSTEM COMMAND DETECTED]\n"
        f"You MUST include: "
        f"[UI_ACTION:{action}:{path}]\n"
        f"Acknowledge naturally."
      )

  elif automation_results:
    for result in automation_results:
      action_type = result.get("action_type", "")
      command = result.get("command", "")
      browser = result.get("browser", "firefox")
      requires_confirm = result.get(
        "requires_confirmation", False
      )
      if action_type == "OPEN_APP":
        automation_context += (
          f"Open {command} → "
          f"[UI_ACTION:open_app:{command}]\n"
        )
      elif action_type == "OPEN_URL":
        automation_context += (
          f"Open {command} in {browser} → "
          f"[UI_ACTION:open_url:{browser}:{command}]\n"
        )
      elif action_type == "SYSTEM_CONTROL":
        if command == "lock_screen":
          automation_context += (
            f"Lock screen → [UI_ACTION:lock_screen]\n"
          )
        elif command.startswith("close_app:"):
          app = command.replace("close_app:", "").strip()
          automation_context += (
            f"Close {app} → [UI_ACTION:close_app:{app}]\n"
          )
        elif command.startswith("volume_"):
          act = command.replace("volume_", "").strip()
          automation_context += (
            f"Set volume {act} → [UI_ACTION:set_volume:{act}]\n"
          )
      elif action_type == "SYSTEM_QUERY":
        if command.startswith("list_dir:"):
          path = command.replace("list_dir:", "").replace("%USERNAME%", os.environ.get("USERNAME", ""))
          automation_context += (
            f"List directory → [UI_ACTION:list_dir:{path}]\n"
          )
        else:
          # Normalize query name
          q = command.strip().lower()
          if q in ("ip", "get_ip", "my_ip"):
            q = "ip_address"
          elif q in ("battery", "get_battery"):
            q = "battery_level"
          elif q in ("disk", "get_disk", "disk_usage"):
            q = "disk_space"
          elif q in ("processes", "cpu", "cpu_usage"):
            q = "top_processes"
          automation_context += (
            f"Query system → [UI_ACTION:system_query:{q}]\n"
          )
      elif requires_confirm:
        automation_context += (
          f"Ask confirmation → "
          f"[UI_ACTION:confirm_action:{command}]\n"
        )
    automation_context = automation_context[:300]

  # Build minimal messages WITH automation context
  personality_mode = await get_setting("personality_mode", settings.PERSONALITY_MODE)
  modifier = await get_setting("modifier", settings.MODIFIER)
  address_preference = await get_setting("address_preference", settings.ADDRESS_PREFERENCE)
  # NOTE: previously truncated to [:500] / UI_ACTION_INSTRUCTION[:300] as a
  # voice-latency measure. That silently cut SYSTEM_CAPABILITIES entirely
  # (personality_mode/modifier UI_ACTION docs don't appear until char ~789
  # of UI_ACTION_INSTRUCTION), so voice commands like "switch to developer
  # mode" got a response denying the capability existed at all. If voice
  # responses need to stay terse, that's a "quiet" modifier / response-
  # length concern, not a reason to hide capabilities from the model.
  system_content = get_system_prompt(personality_mode, modifier, address_preference)
  if automation_context:
    system_content += (
      f"\n\n{automation_context}\n"
      f"Include ALL action tags in response.\n"
      f"Do NOT ask permission - just execute."
    )
  else:
    system_content += f"\n\n{UI_ACTION_INSTRUCTION}"
  # Voice-mode conciseness constraint. Appended after UI_ACTION_INSTRUCTION
  # so it takes effect on every non-automation voice query. The LLM
  # instruction is the primary guard; the hard truncation below is the
  # safety net for when the model ignores it (e.g. "tell me about AI"
  # returning 7000+ chars).
  system_content += (
    "\n\n[VOICE MODE] This response will be spoken aloud by a TTS engine. "
    "Keep it under 3 sentences maximum. "
    "Never give lists, headers, bullet points, or long explanations via voice "
    "\u2014 summarize concisely instead. "
    "Speak directly and conversationally, as if answering out loud."
  )

  minimal_messages = [
    Message(
      role="system",
      content=system_content,
      timestamp=""
    ),
    Message(
      role="user",
      content=text,
      timestamp=""
    )
  ]

  # Web search - same detection/fetch as chat_endpoint (needs_web_search,
  # extract_search_query, search_web with the same 10s timeout and
  # max_results=5), inserted into minimal_messages the same way chat
  # inserts into full_messages (right before the user's own message).
  #
  # Deliberately NOT wired: needs_foreground_search/build_foreground_url.
  # That opens a visible browser tab, which makes sense for chat (there's
  # a UI to show it in) but not for voice - a spoken question shouldn't
  # silently pop a browser window as its answer. Background search
  # (results synthesized into the spoken response) is what a voice query
  # actually needs.
  search_needed = needs_web_search(text)
  if search_needed:
    search_query_used = extract_search_query(text)
    try:
      search_results = await asyncio.wait_for(
        search_web(search_query_used, max_results=5),
        timeout=10.0
      )
      if search_results:
        search_context = (
          f"\n\nWeb search results for '{search_query_used}':\n\n"
        )
        for i, r in enumerate(search_results, 1):
          search_context += (
            f"{i}. Source: {r.get('source', 'Unknown')}\n"
            f"   {r['snippet'][:200]}\n\n"
          )
        # Stricter than chat's "3-4 key points" - this gets read aloud by
        # TTS, not displayed as text a user can skim, so the model needs
        # to synthesize down to something actually speakable rather than
        # a multi-point rundown.
        search_context += (
          "\nInstructions: This will be spoken aloud, not displayed as "
          "text. Answer in 1-2 short spoken sentences using these "
          "results - state the key fact(s) directly, no lists, no "
          "headers, no URLs. Cite a source by name only if it flows "
          "naturally in speech (e.g. 'According to TechCrunch...')."
        )
        search_context = search_context[:1500]
        minimal_messages.insert(-1, Message(
          role="system",
          content=search_context,
          timestamp=""
        ))
    except (asyncio.TimeoutError, Exception) as e:
      print(f"[VOICE] Search error: {e}")

  # Same fallback cascade chat_endpoint/chat_stream_endpoint use - no
  # voice-specific reordering. This used to filter out Gemini entirely
  # and sort Ollama first ("Use ollama first for voice"), which meant
  # voice silently never even tried Gemini/the documented Gemini ->
  # OpenRouter -> Groq -> Ollama cascade, always landing on Ollama (a much
  # smaller local model) whenever it merely wasn't the FIRST option tried,
  # not because the other three had actually failed.
  # Pass providers explicitly (routes.py's own provider_manager reference)
  # rather than letting run_cascade fall back to its own import - fallback.py
  # imports provider_manager independently, so relying on its default here
  # would silently ignore a provider_manager swapped out at this module's
  # name (e.g. in tests, or any future per-request override upstream).
  cascade = await run_cascade(
    minimal_messages, user_text=text, providers=provider_manager.providers
  )

  fallback_occurred = False
  failed_provider = None

  if cascade["status"] == "ok":
    response_text = cascade["response_text"]
    provider_used = cascade["provider_used"]
    model_used = cascade["model_used"]
    fallback_occurred = cascade.get("fallback_occurred", False)
    failed_provider = cascade.get("failed_provider")
    if fallback_occurred and failed_provider:
      # Spoken note, naturally prepended to the actual answer rather than
      # a separate interruption - see routes.py PART 2 in the fallback
      # notification work.
      response_text = build_fallback_note(failed_provider, provider_used) + response_text
    print(f"[VOICE] Used provider: {provider_used}" + (
      f" (after {failed_provider} failed)" if fallback_occurred else ""
    ))
  elif cascade["status"] == "asking":
    response_text = build_ask_message(cascade["failed_provider"], cascade.get("remaining", []))
    provider_used = "asking"
    model_used = "asking"
  elif cascade["status"] == "override_unavailable":
    response_text = build_override_unavailable_message(cascade["failed_provider"])
    provider_used = "override_unavailable"
    model_used = "unavailable"
  else:
    response_text = (
      build_unconfigured_message() if provider_manager.is_unconfigured()
      else "All voice providers unavailable."
    )
    provider_used = "error"
    model_used = "error"

  # Same backend-enforced destructive-action guard /chat and /chat/stream
  # apply. Voice skipped this entirely, which meant a spoken "email Sarah
  # and tell her I quit" produced a raw [UI_ACTION:send_email:...] that the
  # frontend executed on arrival - no confirmation step, no undo, and one
  # misheard transcript away from happening by accident. The voice path is
  # the LEAST trustworthy input in the system (speech recognition errors on
  # top of model errors), so it needs this guard more than chat does, not
  # less. Applied before the briefing prefix and the length cap so the
  # rewritten tag is what gets truncated/broadcast, matching /chat's order.
  response_text = enforce_destructive_confirmation(response_text)

  response_text = briefing_prefix + response_text

  # Hard voice response length cap: even if the LLM ignores the system-prompt
  # conciseness instruction, TTS must never receive an unbounded response.
  # 500 chars ≈ 3–4 short spoken sentences — enough for a complete answer,
  # not a lecture. Snap to the last sentence boundary ('.', '!', '?') within
  # the window to avoid a mid-word cut; fall back to hard slice if none found.
  _VOICE_MAX_CHARS = 500
  if len(response_text) > _VOICE_MAX_CHARS:
    truncated = response_text[:_VOICE_MAX_CHARS]
    # Find the last sentence-ending punctuation to get a clean cut-point.
    last_boundary = max(
      truncated.rfind("."),
      truncated.rfind("!"),
      truncated.rfind("?"),
    )
    if last_boundary > _VOICE_MAX_CHARS // 2:  # only snap if not too short
      truncated = truncated[:last_boundary + 1]
    original_len = len(response_text)
    response_text = truncated
    print(
      f"[VOICE] Response truncated for TTS: "
      f"{original_len} chars → {len(response_text)} chars"
    )

  safe_print(f"[JARVIS VOICE RESPONSE] {response_text}")

  # Broadcast via WebSocket. Keep UI_ACTION tags intact here - the frontend
  # (useJarvisChat.ts) parses and strips them for display itself, and also
  # executes them (personality_mode/modifier switches etc). Pre-stripping
  # them here (as this used to do) silently threw the tag away before the
  # frontend ever saw it, so voice-triggered UI actions never fired even
  # though the LLM correctly emitted them.
  await broadcast_voice_event({
    "type": "voice_input",
    "text": text
  })
  await broadcast_voice_event({
    "type": "voice_response",
    "text": response_text,
    "provider_used": provider_used,
    "model_used": model_used,
    "fallback_occurred": fallback_occurred,
    "failed_provider": failed_provider
  })
  # Note: TTS status (speaking->idle) is handled in main.py callback

  return {
    "response": response_text,
    "conversation_id": "",
    "provider_used": provider_used,
    "model_used": model_used,
    "fallback_occurred": fallback_occurred,
    "failed_provider": failed_provider
  }

@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
  await websocket.accept()
  connected_clients.add(websocket)
  try:
    while True:
      await websocket.receive_text()
  except:
    connected_clients.discard(websocket)

async def broadcast_voice_event(event: dict):
  global _voice_event_seq
  async with _voice_seq_lock:
    _voice_event_seq += 1
    event["seq"] = _voice_event_seq
    event["timestamp"] = time.time()

  dead = set()
  for client in list(connected_clients):
    try:
      await client.send_json(event)
    except:
      dead.add(client)
  connected_clients.difference_update(dead)

PERSONALITY_ASSISTANT_PROMPT = """You are JARVIS, a premium AI desktop assistant for Nithish. You are intelligent, efficient, and highly capable.

Personality:
- Direct and confident, never vague or wishy-washy
- Professional but warm
- Concise — say what needs to be said, nothing more
- {ADDRESS_LINE}
- Never start responses with "Certainly!", "Of course!", "Great!", or similar filler phrases
- When you do not know something, say so directly
- Reference earlier parts of the conversation naturally when relevant
- Do not summarize or recap the conversation history unless the user explicitly asks what has happened so far. For simple greetings or short exchanges, respond briefly and directly — do not restate prior turns.
- When natural, briefly note one relevant follow-up the user might find useful — but don't force it onto every response.

You are not a generic chatbot. You are JARVIS — act like it.
"""

PERSONALITY_DEVELOPER_PROMPT = """You are JARVIS in Developer Mode for Nithish. You are an expert software engineer, systems architect, and technical copilot.

Personality & Tone:
- Technical precision over warmth. Minimize pleasantries, conversational filler, and fluff.
- {ADDRESS_LINE}
- Proactively surface relevant technical details (exact file paths, error specifics, edge cases, performance considerations, and concrete code snippets) without needing to be prompted.
- Provide rigorous, robust solutions with exact syntax, commands, and actionable implementations.
- Do not recap prior conversation turns unless asked.
- When relevant, proactively flag an adjacent technical consideration (an edge case, a related file, a potential issue) the user didn't explicitly ask about but would likely want to know.
"""

PERSONALITY_RESEARCH_PROMPT = """You are JARVIS in Research Mode for Nithish. You are a deep, analytical research assistant and technical investigator.

Personality & Tone:
- Thorough, investigative, and exploratory.
- Willing to conduct multi-step analysis and show your underlying reasoning and chain of thought rather than only giving surface conclusions.
- Actively favor pulling in web search results, citations, and verified references over answering from intuition or memory alone.
- Comfortable with comprehensive, deep-dive responses that analyze trade-offs, literature, and underlying mechanics.
- When relevant, note one adjacent angle or follow-up question worth investigating that the user didn't explicitly ask about.
"""

MODIFIER_PLANNER_PROMPT = """[MODIFIER: PLANNER ACTIVE]
Structure your response as a concrete, actionable plan:
- Break the solution into clear, structured steps, phases, or a done/open breakdown where relevant.
- Explicitly flag weak evidence, unverified assumptions, or potential risks rather than accepting them at face value.
- Frame your answer around plan-before-action and clear execution order.
- Preserve the technical depth and specific tone of the active personality mode.
"""

MODIFIER_QUIET_PROMPT = """[MODIFIER: QUIET ACTIVE]
Respond in the absolute minimum words necessary:
- No proactive suggestions, no 'would you also like...', and no unprompted tangents.
- Answer ONLY what was explicitly asked, as concisely and compactly as possible.
- Omit conversational filler entirely.
"""

JARVIS_SYSTEM_PROMPT = PERSONALITY_ASSISTANT_PROMPT.replace(
    "{ADDRESS_LINE}", 'Occasionally address Nithish as "sir" when natural, not every sentence'
)

def _address_suffix(address_preference: str) -> str:
    """', {addr}' for deterministic (non-LLM) response_text f-strings that
    used to hardcode ', sir' directly - empty string when no address term
    is configured, so output reads as "Opening Chrome. [...]" rather than
    the awkward "Opening Chrome, . [...]".
    """
    addr = (address_preference if address_preference is not None else "").strip()
    return f", {addr}" if addr else ""

def _address_line(address_preference: str, minimal: bool = False) -> str:
    """Builds the address-instruction line substituted into {ADDRESS_LINE}.
    Empty address_preference means no title/name at all - handled
    explicitly here rather than left for the model to improvise, so it
    doesn't produce awkward phrasing like "Hello , how...".
    """
    addr = (address_preference if address_preference is not None else "").strip()
    if not addr:
        return "Address the user directly, with no title or name - do not insert any address term or placeholder"
    if minimal:
        return f'Skip addressing the user as "{addr}" almost entirely; use it rarely, only when natural, communicating peer-to-peer instead'
    return f'Occasionally address the user as "{addr}" when natural, not every sentence'

def get_system_prompt(
    personality_mode: str = "assistant",
    modifier: str = "none",
    address_preference: str = None,
) -> str:
    if address_preference is None:
        address_preference = settings.ADDRESS_PREFERENCE

    mode = (personality_mode or "assistant").lower().strip()
    if mode == "developer":
        base = PERSONALITY_DEVELOPER_PROMPT.replace(
            "{ADDRESS_LINE}", _address_line(address_preference, minimal=True)
        )
    elif mode == "research":
        base = PERSONALITY_RESEARCH_PROMPT
    else:
        base = PERSONALITY_ASSISTANT_PROMPT.replace(
            "{ADDRESS_LINE}", _address_line(address_preference)
        )

    mod = (modifier or "none").lower().strip()
    if mod == "planner":
        prompt = base + "\n" + MODIFIER_PLANNER_PROMPT
    elif mod == "quiet":
        prompt = base + "\n" + MODIFIER_QUIET_PROMPT
    else:
        prompt = base

    from ..plugins.registry import registry
    plugin_caps = registry.get_capabilities_text()
    if plugin_caps:
        prompt = prompt + "\n\n" + plugin_caps

    return prompt

def _notable_system_status() -> str | None:
    """A short note on RAM/disk, but ONLY when genuinely notable (>=90%
    used) - deliberately silent otherwise so the briefing doesn't clutter
    itself with routine numbers every day. Best-effort: any failure (e.g.
    non-Windows, permission issue) just means no note, not a crash - this
    is a "nice to have" addition to the briefing, not a hard dependency.
    """
    notes = []
    try:
        import shutil
        usage = shutil.disk_usage("C:\\")
        pct_used = usage.used / usage.total * 100
        if pct_used >= 90:
            notes.append(f"disk space is at {pct_used:.0f}% used")
    except Exception:
        pass
    try:
        import ctypes

        class _MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        if stat.dwMemoryLoad >= 90:
            notes.append(f"RAM usage is at {stat.dwMemoryLoad}%")
    except Exception:
        pass
    if not notes:
        return None
    return "Heads up: " + " and ".join(notes) + "."

async def _relevant_memory_mention() -> str | None:
    """Surfaces at most one memory, and only when it's clearly important
    (importance >= 7 on the existing 1-10 scale) - a daily briefing that
    mentions every low-importance memory is noise, not a briefing.
    Empty-string query hits get_relevant_memories' "no meaningful words"
    branch, which returns top memories by importance/recency rather than
    doing a keyword match against nothing.
    """
    try:
        memories = await memory_manager.get_relevant_memories("", limit=3)
    except Exception as e:
        print(f"[BRIEFING] Memory lookup failed: {e}")
        return None
    if not memories:
        return None
    top = memories[0]
    if top.get("importance", 0) < 7:
        return None
    return f"Also, you'd mentioned: \"{top['content']}\"."

def _time_of_day_greeting() -> str:
    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"

async def maybe_build_daily_briefing(address_preference: str = None) -> str:
    """Returns a briefing string ready to prepend to the first response of
    the day (ending in a blank line), or "" if none is due right now.

    Deliberately scoped to only what's honestly available today: a
    time-aware greeting, the date, a system-status note if genuinely
    notable, and a relevant-memory mention if one exists. Nothing here is
    LLM-generated - it's plain deterministic Python string building - so
    there is no risk of it fabricating calendar/email/task content that
    doesn't exist yet (that's Phase 8 integration work).

    Marks last_briefing_date as today the moment it decides to fire, so a
    second message the same day (whether via /chat, /chat/stream, or
    /voice/input - all three call this) does not repeat it.
    """
    from datetime import datetime

    enabled = await get_setting(
        "daily_briefing_enabled", settings.DAILY_BRIEFING_ENABLED
    )
    if enabled.strip().lower() != "true":
        return ""

    today_str = datetime.now().strftime("%Y-%m-%d")
    last = await get_setting("last_briefing_date", settings.LAST_BRIEFING_DATE)
    if last == today_str:
        return ""

    await set_setting("last_briefing_date", today_str)

    greeting = _time_of_day_greeting()
    addr = (address_preference if address_preference is not None else "").strip()
    date_str = datetime.now().strftime("%A, %B %d, %Y")

    lines = [f"{greeting}{f', {addr}' if addr else ''}. Today is {date_str}."]

    status_note = _notable_system_status()
    if status_note:
        lines.append(status_note)

    memory_note = await _relevant_memory_mention()
    if memory_note:
        lines.append(memory_note)

    return " ".join(lines) + "\n\n"

def trim_messages_to_budget(messages: list[Message], max_tokens: int = 4000) -> list[Message]:
    """
    Universally caps total payload tokens to `max_tokens` (default ~4000 tokens using len(text)//4).
    If estimated tokens exceed budget, iteratively drops oldest non-system history messages
    (preserving system prompts and the latest user message) until under budget.
    """
    total_tokens = sum(len(m.content) for m in messages) // 4
    if total_tokens <= max_tokens:
        return messages

    msgs = list(messages)
    while total_tokens > max_tokens:
        target_idx = None
        for idx in range(len(msgs) - 1):
            if msgs[idx].role != "system":
                target_idx = idx
                break

        if target_idx is None:
            break

        print(f"[WARNING] Universal payload token budget exceeded ({total_tokens} > {max_tokens}). Trimming oldest history message.")
        msgs.pop(target_idx)
        total_tokens = sum(len(m.content) for m in msgs) // 4

    return msgs

SHORT_SYSTEM_PROMPT = """You are JARVIS, a premium AI assistant.
Be concise, direct, professional. Address user as "sir" occasionally.
Never start with "Certainly!" or "Of course!".
Include [UI_ACTION:tag] only when explicitly asked."""

UI_ACTION_REMINDER = (
    "Remember: [UI_ACTION:tag] controls the interface, only when explicitly requested. "
    "open_app:appname is for REAL desktop apps (notepad, chrome, whatsapp...) - "
    "graph_open_hub:Notes/Skills/Tools/Files/Models is for JARVIS's OWN panels only, never for an app."
)

UI_ACTION_INSTRUCTION = """
<SYSTEM_CAPABILITIES>
Control the JARVIS interface with a [UI_ACTION:tag] placed at the END of your response - only when the user explicitly asks for that action, never while just answering or searching. Never show the raw tag as visible prose; multiple tags may be combined if needed.

[UI_ACTION:chat_mode_on] / [UI_ACTION:chat_mode_off] - toggle full chat mode vs graph mode
[UI_ACTION:graph_expand] / [UI_ACTION:graph_collapse] - expand/collapse the graph
[UI_ACTION:graph_open_hub:Skills|Tools|Files|Notes|Models|Conversations] - open one of JARVIS's OWN internal panels. These are NOT real applications - "notepad" is an app, not the Notes hub.
[UI_ACTION:open_app:appname] - launch a REAL desktop app/program (notepad, calculator, chrome, whatsapp, spotify, discord, vs code, etc.). Use this for any "open/launch/start <app>" request - never graph_open_hub for this.
[UI_ACTION:conversations_open] / [UI_ACTION:conversations_close] - open/close the conversation panel ("chat history", "past chats")
[UI_ACTION:personality_mode:assistant|developer|research] - switch personality mode
[UI_ACTION:modifier:none|planner|quiet] - planner = structured plans; quiet = minimal concise output; none = clear it
[UI_ACTION:address_preference:Name] - set how you address the user; [UI_ACTION:address_preference:] with an empty value clears it entirely ("stop calling me sir")
[UI_ACTION:provider_override:gemini|openrouter|groq|ollama|none] - lock the AI brain to one provider only, or "none" to restore the normal fallback cascade
[UI_ACTION:fallback_mode:auto|ask] - auto-switch providers on failure, or ask before switching
[UI_ACTION:new_chat] / [UI_ACTION:new_chat:Title] - start a fresh conversation, optionally pre-titled
[UI_ACTION:open_chat:Title] - open an existing past chat by (partial) title
[UI_ACTION:rename_chat:Title] - rename the current conversation
[UI_ACTION:delete_conversation:Title] - delete a past conversation by (partial) title
[UI_ACTION:check_github_repos] - List GitHub repositories
[UI_ACTION:check_github_issues:<repo>] - List open GitHub issues for a repository
[UI_ACTION:search_github_issues:<query>] - Search GitHub issues
[UI_ACTION:create_github_issue:<repo>:<title>:<body>] - Create a GitHub issue
[UI_ACTION:check_github_prs:<repo>] - List open GitHub pull requests
[UI_ACTION:check_pr_status:<repo>:<number>] - Check GitHub PR status
[UI_ACTION:search_github_code:<query>:<repo>] - Search GitHub code

Examples:
- "open notepad" -> "Opening Notepad, sir. [UI_ACTION:open_app:notepad]"
- "open whatsapp" -> "Opening WhatsApp, sir. [UI_ACTION:open_app:whatsapp]"
- "open skills" -> "Opening Skills now. [UI_ACTION:graph_open_hub:Skills]"
- "stop calling me sir" -> "Understood, I'll address you directly. [UI_ACTION:address_preference:]"
- "switch to developer mode" -> "Switching to Developer mode. [UI_ACTION:personality_mode:developer]"
- "lock to groq" -> "Locking the AI brain to Groq. [UI_ACTION:provider_override:groq]"
- "delete the 3050 conversation" -> "Initiating deletion for the 3050 conversation. [UI_ACTION:delete_conversation:3050]"
</SYSTEM_CAPABILITIES>
"""
SEARCH_STRICT_INSTRUCTION = """
When web search results are provided:
- Use ONLY information from the search results
- Do NOT add facts from your training data
- NEVER show raw URLs in your response
- NEVER use [URL: ...] format
- Instead cite sources naturally like:
  "According to Reddit..." or
  "The Wall Street Journal reports..."
- Keep responses concise and factual
- Maximum 3-4 bullet points
- End with offering more details
"""

COMMAND_GENERATION_PROMPT = """
Classify this request and return JSON only.

Request: "{request}"

Return ONE JSON object:
{{"action_type":"OPEN_APP|OPEN_URL|SYSTEM_CONTROL|SYSTEM_QUERY|FILE_OP|GMAIL_OP|CALENDAR_OP|WEATHER_OP|GITHUB_OP|UNSAFE",
"command":"app name, url, or fixed query/control enum",
"browser":"firefox",
"description":"brief description",
"requires_confirmation":false,
"display_output":false}}

Rules for SYSTEM_QUERY:
- Use fixed query names for command: "ip_address", "battery_level", "disk_space", "top_processes", "uptime", or "list_dir:<path>"
- NEVER output raw PowerShell commands.

Rules for SYSTEM_CONTROL:
- Use fixed command names: "lock_screen", "close_app:<name>", "volume_up", "volume_down", "volume_mute"

Rules for FILE_OP (paths are Windows, NEVER Linux/macOS style):
- command must be one of: "create_folder:<path>", "delete_file:<path>", "open_file:<path>", "show_explorer:<path>"
- <path> MUST use Windows backslashes and a drive letter, in the form: C:\\Users\\%USERNAME%\\<Folder>\\<name>
- Use the literal placeholder %USERNAME% for the user's home folder - do NOT invent a username.
- Valid <Folder> values: Desktop, Downloads, Documents, Pictures, Music, Videos
- NEVER output a path starting with "/", "/home/", "~/", or any other non-Windows form.
- requires_confirmation is ADVISORY ONLY for delete_file - the backend always requires confirmation for deletes regardless of this field, so set it to true anyway for accuracy.

Rules for GMAIL_OP:
- command must be one of: "check_gmail", "search_gmail:<query>", "send_email:<to>:<subject>:<body>"
- For send_email, requires_confirmation MUST be true.

Rules for CALENDAR_OP:
- command must be one of: "check_calendar", "check_upcoming_events", "create_event:<title>:<start>:<end>"
- For create_event, requires_confirmation MUST be true.
- <start> and <end> should be ISO format strings if possible.

Rules for WEATHER_OP:
- command must be one of: "check_weather", "check_weather:<location>", "check_forecast:<location>:<days>"

Rules for GITHUB_OP:
- command must be one of: "check_github_repos", "check_github_issues:<repo>", "search_github_issues:<query>", "create_github_issue:<repo>:<title>:<body>", "check_github_prs:<repo>", "check_pr_status:<repo>:<number>", "search_github_code:<query>:<repo>"
- For create_github_issue, requires_confirmation MUST be true.

Examples:
open chrome → {{"action_type":"OPEN_APP","command":"chrome","browser":"firefox","description":"Open Chrome","requires_confirmation":false,"display_output":false}}
close chrome → {{"action_type":"SYSTEM_CONTROL","command":"close_app:chrome","browser":"firefox","description":"Close Chrome","requires_confirmation":false,"display_output":false}}
lock screen → {{"action_type":"SYSTEM_CONTROL","command":"lock_screen","browser":"firefox","description":"Lock Screen","requires_confirmation":false,"display_output":false}}
what is my IP → {{"action_type":"SYSTEM_QUERY","command":"ip_address","browser":"firefox","description":"Get IP Address","requires_confirmation":false,"display_output":true}}
top cpu processes → {{"action_type":"SYSTEM_QUERY","command":"top_processes","browser":"firefox","description":"Get Top CPU Processes","requires_confirmation":false,"display_output":true}}
check battery → {{"action_type":"SYSTEM_QUERY","command":"battery_level","browser":"firefox","description":"Get Battery Level","requires_confirmation":false,"display_output":true}}
check disk space → {{"action_type":"SYSTEM_QUERY","command":"disk_space","browser":"firefox","description":"Get Disk Space","requires_confirmation":false,"display_output":true}}
delete test.txt on my desktop → {{"action_type":"FILE_OP","command":"delete_file:C:\\\\Users\\\\%USERNAME%\\\\Desktop\\\\test.txt","browser":"firefox","description":"Delete test.txt from Desktop","requires_confirmation":true,"display_output":false}}
check my emails → {{"action_type":"GMAIL_OP","command":"check_gmail","browser":"firefox","description":"Check emails","requires_confirmation":false,"display_output":true}}
what is on my calendar today → {{"action_type":"CALENDAR_OP","command":"check_calendar","browser":"firefox","description":"Check calendar","requires_confirmation":false,"display_output":true}}
send an email to test@example.com saying hello → {{"action_type":"GMAIL_OP","command":"send_email:test@example.com:Hello:Hello there","browser":"firefox","description":"Send email","requires_confirmation":true,"display_output":false}}
weather in Paris → {{"action_type":"WEATHER_OP","command":"check_weather:Paris","browser":"firefox","description":"Check weather in Paris","requires_confirmation":false,"display_output":true}}
forecast for London for 3 days → {{"action_type":"WEATHER_OP","command":"check_forecast:London:3","browser":"firefox","description":"Check 3-day forecast for London","requires_confirmation":false,"display_output":true}}
"""

FOREGROUND_TRIGGERS = [
  "show me", "show me on",
  "in the foreground", "foreground search",
  "search on youtube", "search on google",
  "search youtube for", "search google for",
  "find on youtube", "look up on youtube",
  "play on youtube", "watch on youtube",
  "youtube for", "on youtube",
  "on google", "google for",
  "in firefox", "in chrome", "in edge",
  "in browser", "open browser and search",
  "open google", "open amazon", "open youtube",
  "open netflix", "open twitter",
  "open instagram", "open facebook",
  "open linkedin", "open github",
  "open reddit", "open stackoverflow",
  "open whatsapp web", "open gmail",
  "open maps", "open google maps",
]

def needs_foreground_search(
  message: str
) -> bool:
  msg_lower = message.lower().strip()
  
  # Don't trigger for graph UI commands
  ui_words = [
    "graph", "skills", "tools", "notes",
    "models", "chat mode", "graph mode",
    "conversations"
  ]
  for ui in ui_words:
    if ui in msg_lower:
      return False
  
  # Don't trigger if automation handles it
  # (open_app already handles specific apps)
  if needs_automation(msg_lower):
    # But DO trigger if it's a URL/search
    # in a browser
    for trigger in FOREGROUND_TRIGGERS:
      if trigger in msg_lower:
        return True
    return False
  
  for trigger in FOREGROUND_TRIGGERS:
    if trigger in msg_lower:
      return True
  return False

def build_foreground_url(
  message: str
) -> dict:
  msg_lower = message.lower().strip()
  
  # YouTube patterns
  yt_triggers = [
    "on youtube", "youtube for",
    "search youtube", "find on youtube",
    "play on youtube", "watch on youtube",
    "search on youtube", "search youtube for",
    "open youtube",
  ]
  for t in yt_triggers:
    if t in msg_lower:
      # Start with original message
      query = message.strip()
      
      # Remove these phrases in order
      phrases_to_remove = [
        "open youtube and search ",
        "open youtube and search",
        "open youtube to search ",
        "open youtube to find ",
        "and search ",
        "and find ",
        "and play ",
        "and watch ",
        "search youtube for ", "search youtube for",
        "search on youtube for ", 
        "search on youtube ",
        "search on youtube",
        "find on youtube ", "find on youtube",
        "play on youtube ", "play on youtube",
        "watch on youtube ", "watch on youtube",
        "look up on youtube ", 
        "youtube for ", "youtube for",
        "on youtube", "youtube",
        "show me ", "search for ",
        "search ", "find ", "play ",
        "watch ", "look up ",
        "open youtube ",
      ]

      for phrase in phrases_to_remove:
        # Case insensitive replacement
        import re
        query = re.sub(
          re.escape(phrase),
          "",
          query,
          flags=re.IGNORECASE
        ).strip()
      
      # Clean up extra spaces and punctuation
      query = query.strip(" .,!?").strip()
      
      # Replace spaces with + for URL
      query_encoded = query.replace(" ", "+")
      
      print(f"YouTube query extracted: '{query}'")
      
      if not query_encoded:
        return {
          "url": "https://youtube.com",
          "browser": "firefox",
          "description": "Opening YouTube"
        }
      return {
        "url": f"https://youtube.com/results?search_query={query_encoded}",
        "browser": "firefox",
        "description": f"Searching YouTube for {query}"
      }
  
  # Google patterns
  google_triggers = [
    "on google", "google for",
    "search on google", "search google for",
    "open google",
  ]
  for t in google_triggers:
    if t in msg_lower:
      query = msg_lower
      for remove in [
        "show me ", "search ", "find ",
        "on google", "google for ",
        "search on google ", "search google for ",
        "open google and search ",
        "open google",
      ]:
        query = query.replace(remove, "")
      query = query.strip().replace(" ", "+")
      if not query:
        return {
          "url": "https://google.com",
          "browser": "firefox",
          "description": "Opening Google"
        }
      return {
        "url": f"https://google.com/search?q={query}",
        "browser": "firefox",
        "description": f"Searching Google for {query.replace('+', ' ')}"
      }
  
  # Common websites
  site_map = {
    "gmail": "https://gmail.com",
    "amazon": "https://amazon.in",
    "netflix": "https://netflix.com",
    "twitter": "https://twitter.com",
    "instagram": "https://instagram.com",
    "facebook": "https://facebook.com",
    "linkedin": "https://linkedin.com",
    "github": "https://github.com",
    "reddit": "https://reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "whatsapp": "https://web.whatsapp.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
  }
  for site, url in site_map.items():
    if site in msg_lower:
      return {
        "url": url,
        "browser": "firefox",
        "description": f"Opening {site.title()}"
      }
  
  # "show me X" - generic Google search
  if msg_lower.startswith("show me "):
    query = message[8:].strip().replace(" ", "+")
    return {
      "url": f"https://google.com/search?q={query}",
      "browser": "firefox",
      "description": f"Showing {message[8:].strip()} in browser"
    }
  
  # Default - Google search
  query = message.strip().replace(" ", "+")
  return {
    "url": f"https://google.com/search?q={query}",
    "browser": "firefox",
    "description": f"Searching for {message.strip()}"
  }

# SINGLE SOURCE OF TRUTH for which UI actions may never reach the frontend
# unconfirmed. enforce_destructive_confirmation() below is generated from
# this tuple - there is no per-action code path - so adding a new plugin's
# destructive action means adding one string HERE and registering a
# confirm handler in the frontend's actionSafety.ts. Nothing else.
#
# Deliberately NOT listed: delete_conversation and delete_memory. Those are
# already gated by a real server-side PIN check on their own endpoints
# (see delete_conversation_endpoint / delete_memory_endpoint), so wrapping
# them here would stack a second, weaker gate in front of a stronger one.
# The frontend still routes delete_conversation through confirmation on the
# voice path specifically - see VOICE_CONFIRM_ACTIONS in actionSafety.ts.
DESTRUCTIVE_UI_ACTIONS = (
  "delete_file",
  "send_email",
  "create_event",
  "create_github_issue",
)

DESTRUCTIVE_PATTERNS = [
  r'\bdelete\b', r'\bremove\b', r'\bkill\b',
  r'\bterminate\b', r'\bshutdown\b',
  r'\brestart\b', r'\bformat\b', r'\bclear\b',
  r'\buninstall\b', r'\bwipe\b', r'\berase\b',
  r'\bclose\s+(?:all|every)\b',
  r'\bend\s+(?:process|task)\b',
]

async def detect_and_log_gap(response_text: str, user_request: str) -> str:
    """Backend gap detection (Phase 9)."""
    if "[UI_ACTION:" in response_text:
        return response_text

    import re
    from datetime import datetime, timezone
    uncertainty_patterns = [
        r"i can\'t",
        r"i cannot",
        r"i don\'t have the ability",
        r"i am not able to",
        r"i\'m not able to",
        r"that\'s beyond my current",
        r"that is beyond my current",
        r"i do not have the ability",
        r"not supported",
        r"i do not have access",
        r"i am unable"
    ]
    
    msg_lower = response_text.lower()
    for pattern in uncertainty_patterns:
        if re.search(pattern, msg_lower):
            import uuid
            gap_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            from ..core.config import settings
            import aiosqlite
            try:
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute(
                        "INSERT INTO gap_log (gap_id, user_request, detected_intent, gap_reason, timestamp, resolved) VALUES (?, ?, ?, ?, ?, ?)",
                        (gap_id, user_request, None, response_text, timestamp, False)
                    )
                    await db.commit()
            except Exception as e:
                print(f"[GAP LOG ERROR] {e}")

            # Broadcast event for UI
            await broadcast_voice_event({
                "type": "gap_detected",
                "request": user_request,
                "timestamp": timestamp
            })

            return response_text + "\n\n(This isn't something I can do yet — I've noted it for future development.)"

    return response_text

def enforce_destructive_confirmation(text: str) -> str:
  """Backend-level guard: a raw, unconfirmed [UI_ACTION:delete_file:...]
  tag must never leave this service, regardless of which code path
  produced it - the deterministic fs_context prompt (which only tells the
  model to use confirm_action, it doesn't enforce it), the LLM-generated
  automation FILE_OP branch, or a hallucinated tag from free-form
  generation. This is the actual enforcement point; prompt text alone is
  just a request the model can ignore.

  Rewrites to confirm_action rather than stripping, so the existing
  two-step UX (frontend shows "reply yes to confirm") still fires - it
  just can no longer be bypassed by the model skipping that step itself.

  Driven entirely by DESTRUCTIVE_UI_ACTIONS. This used to be four
  copy-pasted regex blocks, one per action, which is exactly how
  create_github_issue ended up rewritten here but with no matching
  execution handler on the frontend - the per-action shape made it
  possible to add half a feature. Adding an action is now a one-line
  change to that tuple.

  Every call site that produces user-facing text must run this. Missing
  it is not a degraded response, it is an unconfirmed destructive action:
  /voice/input skipped this for its entire existence and could send email
  straight off a transcript.
  """
  import re

  def _make_rewriter(action_name: str):
    def _rewrite(match):
      payload = match.group(1)
      print(
        f"[SAFETY] Blocked unconfirmed {action_name} UI_ACTION for "
        f"'{payload}' - rewriting to require confirmation"
      )
      return f"[UI_ACTION:confirm_action:{action_name}:{payload}]"
    return _rewrite

  for action_name in DESTRUCTIVE_UI_ACTIONS:
    text = re.sub(
      rf'\[UI_ACTION:{re.escape(action_name)}:([^\]]+)\]',
      _make_rewriter(action_name),
      text,
    )

  return text

def is_destructive_action(message: str) -> bool:
  """
  Checks if a message contains destructive
  action patterns that require confirmation.
  """
  import re
  msg_lower = message.lower()
  for pattern in DESTRUCTIVE_PATTERNS:
    if re.search(pattern, msg_lower):
      return True
  return False

def is_file_system_command(
  message: str
) -> tuple[bool, dict]:
  """
  Returns (is_file_cmd, action_dict)
  Handles file system commands directly
  without going through LLM generation.
  """
  import os
  username = os.environ.get("USERNAME", "")
  msg_lower = message.lower().strip()

  # Common paths
  desktop = f"C:\\Users\\{username}\\Desktop"
  downloads = f"C:\\Users\\{username}\\Downloads"
  documents = f"C:\\Users\\{username}\\Documents"
  pictures = f"C:\\Users\\{username}\\Pictures"
  music = f"C:\\Users\\{username}\\Music"
  videos = f"C:\\Users\\{username}\\Videos"
  
  # LIST DIRECTORY patterns
  list_patterns = {
    "desktop": desktop,
    "downloads": downloads,
    "documents": documents,
    "pictures": pictures,
    "music": music,
    "videos": videos,
  }
  
  list_triggers = [
    "show my ", "list my ", "show files in",
    "what files", "list files", "show files",
    "what's in my ", "whats in my ",
    "what is in my ", "files on my ",
    "show me my ", "open my files",
  ]
  
  for trigger in list_triggers:
    if trigger in msg_lower:
      for folder_name, folder_path in \
          list_patterns.items():
        if folder_name in msg_lower:
          return True, {
            "action": "list_dir",
            "path": folder_path,
            "description": f"Listing {folder_name}"
          }
  
  # CREATE FOLDER patterns
  create_triggers = [
    "create folder", "create a folder",
    "make folder", "make a folder",
    "new folder", "create directory",
  ]
  for trigger in create_triggers:
    if trigger in msg_lower:
      # Extract folder name and location
      import re
      # Pattern: create folder X on/in Desktop
      # Use original message to preserve case
      match = re.search(
        r'(?:create|make)\s+(?:a\s+)?'
        r'(?:folder|directory)\s+'
        r'(?:called\s+|named\s+)?'
        r'([\'"]?)([\w][\w\s\-]*?)\1'
        r'\s+(?:on|in|at)\s+(\w+)',
        message,  # Use original message not msg_lower
        re.IGNORECASE
      )
      if match:
        folder_name = match.group(2).strip()
        location = match.group(3).strip().lower()
        base_path = list_patterns.get(
          location, desktop
        )
        full_path = f"{base_path}\\{folder_name}"
        return True, {
          "action": "create_folder",
          "path": full_path,
          "description": f"Creating folder '{folder_name}'"
        }
  
  # DELETE FILE/FOLDER patterns - ENHANCED
  delete_triggers = [
    "delete ", "remove ", "delete the ",
    "remove the ", "delete my ", "remove my ",
    "delete this ", "remove this ",
  ]
  for trigger in delete_triggers:
    if trigger in msg_lower:
      # Try to extract item name and location
      import re

      # Pattern 1: "delete X in/from/on location"
      match1 = re.search(
        r'(?:delete|remove)\s+(?:the\s+|my\s+|this\s+)?'
        r'(?:file\s+|folder\s+)?'
        r'([\'"]?)([\w][\w\s\.\-]+?)\1'
        r'\s+(?:in|from|on|at)\s+(\w+)',
        message,
        re.IGNORECASE
      )

      # Pattern 2: "delete X" (search all common locations)
      match2 = re.search(
        r'(?:delete|remove)\s+(?:the\s+|my\s+|this\s+)?'
        r'(?:file\s+|folder\s+)?'
        r'([\'"]?)([\w][\w\s\.\-]+?)\1',
        message,
        re.IGNORECASE
      )

      item_name = None
      location = None

      if match1:
        item_name = match1.group(2).strip()
        location = match1.group(3).strip().lower()
      elif match2:
        item_name = match2.group(2).strip()

      if not item_name:
        continue

      # Search locations
      search_locations = []
      if location and location in list_patterns:
        # Specific location requested
        search_locations = [(location, list_patterns[location])]
      else:
        # Search all common locations
        search_locations = list(list_patterns.items())

      # Search for the item
      for loc_name, loc_path in search_locations:
        full_path = f"{loc_path}\\{item_name}"

        # Check if exists (file or folder)
        import os
        if os.path.exists(full_path):
          is_dir = os.path.isdir(full_path)
          item_type = "folder" if is_dir else "file"
          return True, {
            "action": "delete_file",
            "path": full_path,
            "description": f"Delete {item_type} '{item_name}' from {loc_name}",
            "requires_confirmation": True
          }

      # Not found - let LLM handle it
      continue

  return False, {}

def needs_automation(message: str) -> bool:
  msg_lower = message.lower().strip()
  
  # Never trigger automation for questions
  # about availability or information
  question_patterns = [
    "is ", "are ", "does ", "do ",
    "can ", "will ", "should ",
    "what is", "how much", "how many",
    "available", "exist", "support",
  ]
  
  # If message starts with question word
  # and contains "store" or "available"
  # it's a search query not automation
  for q in question_patterns:
    if msg_lower.startswith(q) and (
      "available" in msg_lower or
      "exist" in msg_lower or
      "support" in msg_lower
    ):
      return False
  
  # Existing automation triggers
  automation_triggers = [
    "show my desktop", "show my downloads",
    "show my documents", "show my files",
    "list my files", "list files in",
    "what files", "files on my desktop",
    "files in my downloads",
    "delete file", "delete the file",
    "delete folder", "create folder",
    "make folder", "new folder",
    "open the file", "read the file",
    "show in explorer",
    "list ", "show files", "show folders",
    "what files", "what's in",
    "create folder", "make folder",
    "new folder", "delete file",
    "delete folder", "rename ",
    "open file", "read file",
    "show in explorer", "show desktop files",
    "show downloads", "show documents",
    "open ", "launch ", "start ", "run ",
    "close ", "kill ", "stop ",
    "lock ", "unlock ",
    "create ", "make ", "new folder",
    "delete ", "remove ", "move ", "copy ",
    "what processes", "cpu usage",
    "ip address", "disk space",
    "volume ", "mute ", "unmute ",
    "screenshot", "restart ", "shutdown ",
    "install ", "uninstall ",
    "check email", "check my email",
    "read email", "read my email",
    "search email", "send email", "send an email",
    "check calendar", "what's on my calendar",
    "upcoming event", "create event",
  ]
  
  # Don't trigger for graph/UI commands
  ui_words = [
    "graph", "skills", "tools", "notes",
    "models", "chat mode", "graph mode",
    "conversations panel",
  ]
  for ui in ui_words:
    if ui in msg_lower:
      return False
  
  for trigger in automation_triggers:
    if trigger in msg_lower:
      return True
  return False

async def get_automation_context_str(automation_results: list[dict]) -> str:
    """
    Build automation context string with intelligent trimming
    to keep total size under 400 chars.
    """
    import os

    lines = []
    username = os.environ.get("USERNAME", "")

    for result in automation_results:
        action_type = result.get("action_type", "")
        command = result.get("command", "")
        browser = result.get("browser", "firefox")
        requires_confirm = result.get("requires_confirmation", False)

        if action_type == "OPEN_APP":
            lines.append(f"[UI_ACTION:open_app:{command}]")
        elif action_type == "OPEN_URL":
            lines.append(f"[UI_ACTION:open_url:{browser}:{command}]")
        elif action_type == "SYSTEM_CONTROL":
            if command == "lock_screen":
                lines.append("[UI_ACTION:lock_screen]")
            elif command.startswith("close_app:"):
                app = command.replace("close_app:", "").strip()
                lines.append(f"[UI_ACTION:close_app:{app}]")
            elif command.startswith("volume_"):
                act = command.replace("volume_", "").strip()
                lines.append(f"[UI_ACTION:set_volume:{act}]")
            else:
                lines.append(f"[UI_ACTION:{command}]")
        elif action_type == "SYSTEM_QUERY":
            cmd = result.get("command", "").strip()
            if cmd.startswith("list_dir:"):
                path = cmd.replace("list_dir:", "").replace("%USERNAME%", username)
                lines.append(f"[UI_ACTION:list_dir:{path}]")
            elif cmd in ("ip_address", "ip", "get_ip"):
                lines.append("[UI_ACTION:system_query:ip_address]")
            elif cmd in ("top_processes", "cpu_usage", "processes"):
                lines.append("[UI_ACTION:system_query:top_processes]")
            elif cmd in ("battery_level", "battery", "get_battery"):
                lines.append("[UI_ACTION:system_query:battery_level]")
            elif cmd in ("disk_space", "disk", "get_disk"):
                lines.append("[UI_ACTION:system_query:disk_space]")
            elif cmd in ("uptime", "system_uptime"):
                lines.append("[UI_ACTION:system_query:uptime]")
            else:
                lines.append(f"[UI_ACTION:system_query:{cmd}]")
        elif action_type == "FILE_OP":
            cmd = result.get("command", "")
            if cmd.startswith("create_folder:"):
                path = cmd.replace("create_folder:", "").replace("%USERNAME%", username)
                lines.append(f"[UI_ACTION:create_folder:{path}]")
            elif cmd.startswith("delete_file:"):
                # Destructive - always require confirmation. Unlike the
                # other FILE_OP branches, this must NOT trust whatever
                # requires_confirmation the model returned; delete is
                # inherently destructive regardless of what it claims.
                path = cmd.replace("delete_file:", "").replace("%USERNAME%", username)
                lines.append(f"[UI_ACTION:confirm_action:delete_file:{path}]")
            elif cmd.startswith("open_file:"):
                path = cmd.replace("open_file:", "")
                lines.append(f"[UI_ACTION:open_file:{path}]")
            elif cmd.startswith("show_explorer:"):
                path = cmd.replace("show_explorer:", "")
                lines.append(f"[UI_ACTION:show_explorer:{path}]")
            elif requires_confirm:
                lines.append(f"[UI_ACTION:confirm_action:{cmd[:40]}]")
        elif action_type == "GMAIL_OP":
            cmd = result.get("command", "")
            if cmd.startswith("send_email:"):
                payload = cmd.replace("send_email:", "")
                lines.append(f"[UI_ACTION:confirm_action:send_email:{payload}]")
            else:
                lines.append(f"[UI_ACTION:{cmd}]")
        elif action_type == "CALENDAR_OP":
            cmd = result.get("command", "")
            if cmd.startswith("create_event:"):
                payload = cmd.replace("create_event:", "")
                lines.append(f"[UI_ACTION:confirm_action:create_event:{payload}]")
            else:
                lines.append(f"[UI_ACTION:{cmd}]")
        elif requires_confirm:
            lines.append(f"[UI_ACTION:confirm_action:{command[:40]}]")

    # Build context with header
    automation_context = "[TASK] Include these tags:\n" + "\n".join(lines)

    # Trim to 380 chars max (leaving room for variation)
    if len(automation_context) > 380:
        # Keep first action and indicate more
        first_line = lines[0] if lines else ""
        automation_context = (
            f"[TASK] Include: {first_line}"
            f" (+{len(lines)-1} more)"
        )

    return automation_context


def deduplicate_actions(
  results: list[dict]
) -> list[dict]:
  if not results:
    return results
  
  # Step 1: Find all browsers that have
  # a URL to open
  browsers_opening_url = set()
  for r in results:
    if r.get("action_type") == "OPEN_URL":
      browser = r.get("browser", "firefox")\
        .lower().strip()
      # Normalize browser names
      if any(x in browser for x in 
             ["firefox", "mozilla"]):
        browsers_opening_url.add("firefox")
      elif any(x in browser for x in 
               ["edge", "microsoft"]):
        browsers_opening_url.add("edge")
      elif any(x in browser for x in 
               ["chrome", "google"]):
        browsers_opening_url.add("chrome")
      else:
        browsers_opening_url.add(browser)
  
  if not browsers_opening_url:
    return results
  
  # Step 2: Remove OPEN_APP for any browser
  # that already has an OPEN_URL
  filtered = []
  for r in results:
    if r.get("action_type") != "OPEN_APP":
      filtered.append(r)
      continue
    
    # Check if this app is a browser that
    # already has a URL opening
    app_name = r.get("command", "")\
      .lower().strip()
    
    is_duplicate_browser = False
    
    if "firefox" in browsers_opening_url or \
       "mozilla" in browsers_opening_url:
      if any(x in app_name for x in 
             ["firefox", "mozilla"]):
        is_duplicate_browser = True
    
    if "edge" in browsers_opening_url:
      if any(x in app_name for x in 
             ["edge", "msedge"]):
        is_duplicate_browser = True
    
    if "chrome" in browsers_opening_url:
      if any(x in app_name for x in 
             ["chrome"]):
        is_duplicate_browser = True
    
    if not is_duplicate_browser:
      filtered.append(r)
  
  return filtered

def remove_duplicate_apps(
  results: list[dict]
) -> list[dict]:
  seen_apps = set()
  seen_urls = set()
  filtered = []
  
  for r in results:
    action_type = r.get("action_type", "")
    
    if action_type == "OPEN_APP":
      app = r.get("command", "").lower().strip()
      if app not in seen_apps:
        seen_apps.add(app)
        filtered.append(r)
      # else: skip duplicate
      
    elif action_type == "OPEN_URL":
      url = r.get("command", "").lower().strip()
      if url not in seen_urls:
        seen_urls.add(url)
        filtered.append(r)
      # else: skip duplicate
      
    else:
      filtered.append(r)
  
  return filtered


async def generate_automation_command(
  message: str,
  groq_api_key: str
) -> list[dict]:
  try:
    from groq import Groq
    client = Groq(api_key=groq_api_key)
    
    response = await asyncio.to_thread(
      client.chat.completions.create,
      model="groq/compound",
      messages=[{
        "role": "user",
        "content": COMMAND_GENERATION_PROMPT.replace(
          "{request}", message
        )
      }],
      max_tokens=500,
      temperature=0
    )
    
    text = response.choices[0].message.content.strip()
    import re
    automation_results = []
    arr_match = re.search(r'\[.*\]', text, re.DOTALL)
    obj_match = re.search(r'\{.*\}', text, re.DOTALL)
    
    if arr_match:
      parsed = json_module.loads(arr_match.group())
      if isinstance(parsed, list):
        automation_results = parsed
    # Try single object
    elif obj_match:
      automation_results = [json_module.loads(obj_match.group())]
      
    print(f"Raw automation results: {automation_results}")
    automation_results = deduplicate_actions(automation_results)
    automation_results = remove_duplicate_apps(automation_results)
    print(f"After dedup: {automation_results}")
    
    return automation_results
    
  except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Command generation error: {e}")
    return []


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    conversation_id_exists = request.conversation_id is not None
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Daily briefing check - computed once up front so it applies
    # uniformly to whichever response path this request ends up taking
    # (pure automation, file command, or the general LLM path).
    briefing_address_preference = await get_setting(
        "address_preference", settings.ADDRESS_PREFERENCE
    )
    briefing_prefix = await maybe_build_daily_briefing(briefing_address_preference)

    # Get relevant memories
    relevant_memories = await memory_manager.get_relevant_memories(request.message, limit=5)
    memory_context = ""
    if relevant_memories:
        memory_lines = [f"- {m['content']}" for m in relevant_memories]
        memory_context = "\n\nRelevant memories about Nithish:\n" + "\n".join(memory_lines)
    
    search_performed = False
    search_query_used = ""
    search_sources = []
    
    # Load existing conversation history
    history = []
    search_context_accumulated = ""
    if conversation_id_exists:
        history = await get_conversation_messages(conversation_id)
        system_msgs = [m for m in history if m.role == "system"]
        history = [m for m in history if m.role != "system"]
        if system_msgs:
            recent_system_msgs = system_msgs[-2:]
            search_context_accumulated = "\n\n" + "\n".join(m.content for m in recent_system_msgs)
            search_context_accumulated += "\n" + SEARCH_STRICT_INSTRUCTION
            
        # Universal history cap: Keep only the last 12 user/assistant turn-pairs (24 messages)
        history = history[-24:]
            
    active_provider = provider_manager.providers[0]
    available_providers = ", ".join(p.name.title() for p in provider_manager.providers)
    system_state = f"\n<SYSTEM_STATE>\nActive AI Brain (Provider): {active_provider.name.title()}\nActive Model: {active_provider.model}\nAvailable Brains: {available_providers}\n</SYSTEM_STATE>\n"

    personality_mode = await get_setting("personality_mode", settings.PERSONALITY_MODE)
    modifier = await get_setting("modifier", settings.MODIFIER)
    address_preference = await get_setting("address_preference", settings.ADDRESS_PREFERENCE)
    base_prompt = get_system_prompt(personality_mode, modifier, address_preference)

    system_message = Message(
        role="system",
        content=base_prompt + memory_context + search_context_accumulated + "\n" + UI_ACTION_INSTRUCTION + system_state,
        timestamp=""
    )
        
    # Create new user message
    new_user_message = Message(
        role="user",
        content=request.message,
        timestamp=""
    )
    
    system_message.content += "\n\n" + UI_ACTION_REMINDER
    
    # Build full message list and apply universal token-budget guard
    full_messages = [system_message] + history + [new_user_message]
    full_messages = trim_messages_to_budget(full_messages, max_tokens=4000)
    
    # Save user message to DB
    await save_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )

    # Check file system commands first
    is_file_cmd, file_action = is_file_system_command(request.message)
    automation_results = []

    if is_file_cmd:
        action = file_action["action"]
        path = file_action.get("path", "")
        description = file_action.get("description", "")
        requires_confirm = file_action.get("requires_confirmation", False)

        # Enhanced safety check
        is_destructive = is_destructive_action(request.message)

        if requires_confirm or is_destructive:
            fs_context = (
                f"[SAFETY CHECK REQUIRED]\n"
                f"This action is destructive and irreversible.\n"
                f"You MUST ask the user to confirm.\n"
                f"Say EXACTLY what will be deleted/affected.\n"
                f"Ask: 'Are you sure? Reply YES to confirm or NO to cancel.'\n"
                f"Include: [UI_ACTION:confirm_action:{action}:{path}]\n"
                f"DO NOT execute the action yet."
            )
        else:
            fs_context = (
                f"[FILE SYSTEM COMMAND DETECTED]\n"
                f"You MUST include this EXACT tag:\n"
                f"[UI_ACTION:{action}:{path}]\n"
                f"Acknowledge naturally. No graph actions."
            )

        # Use MINIMAL context for file commands
        # Skip conversation history, memory, search context - but still use
        # the real personality/modifier prompt (already fetched above),
        # not the hardcoded default, and no truncation (see /voice/input's
        # matching fix for why: truncating the prompt/capabilities silently
        # drops functionality rather than shortening tone).
        minimal_messages = [
            Message(
                role="system",
                content=get_system_prompt(personality_mode, modifier, address_preference),
                timestamp=""
            ),
            Message(
                role="system",
                content=fs_context,
                timestamp=""
            ),
            Message(
                role="user",
                content=request.message,
                timestamp=""
            )
        ]

        # Override full_messages with minimal context
        full_messages = minimal_messages
        search_needed = False
    else:
        # Check for automation intent
        if needs_automation(request.message) and settings.GROQ_API_KEY:
            automation_results = await generate_automation_command(
                request.message,
                settings.GROQ_API_KEY
            )

        if automation_results:
            automation_context = await get_automation_context_str(automation_results)
            full_messages.insert(-1, Message(
                role="system",
                content=automation_context,
                timestamp=""
            ))

    # Check if this is a pure automation command that doesn't need AI (voice_input)
    is_pure_automation = (
        len(automation_results) > 0 and
        all(r.get("action_type") in [
            "OPEN_APP", "OPEN_URL",
            "SYSTEM_CONTROL", "lock_screen"
        ] for r in automation_results)
    )

    if is_pure_automation:
        # Build response without AI
        descriptions = [
            r.get("description", "Done")
            for r in automation_results
        ]

        # Build UI action tags
        action_tags = ""
        for result in automation_results:
            action_type = result.get("action_type")
            command = result.get("command", "")
            browser = result.get("browser", "firefox")

            if action_type == "OPEN_APP":
                action_tags += f"[UI_ACTION:open_app:{command}]"
            elif action_type == "OPEN_URL":
                action_tags += f"[UI_ACTION:open_url:{browser}:{command}]"
            elif action_type == "SYSTEM_CONTROL":
                if command == "lock_screen":
                    action_tags += "[UI_ACTION:lock_screen]"

        # Build natural response
        if len(descriptions) == 1:
            response_text = f"{descriptions[0]}{_address_suffix(address_preference)}. {action_tags}"
        else:
            items = ", ".join(descriptions[:-1])
            items += f" and {descriptions[-1]}"
            response_text = f"Opening {items}{_address_suffix(address_preference)}. {action_tags}"

        response_text = briefing_prefix + response_text

        # Broadcast and return
        await broadcast_voice_event({
            "type": "voice_input",
            "text": request.message
        })
        await broadcast_voice_event({
            "type": "voice_response",
            "text": response_text
        })

        # Speak the response via TTS
        import re
        import threading
        from ..voice.tts_engine import tts_engine

        def speak_direct():
            clean = re.sub(
                r'\[UI_ACTION:[^\]]*\]', '', response_text
            ).strip()
            if clean:
                tts_engine.speak_sync(clean)

        t = threading.Thread(target=speak_direct, daemon=True)
        t.start()

        # Save assistant message to DB
        await save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            provider_used="direct",
            model_used="automation"
        )

        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "provider_used": "direct",
            "model_used": "automation"
        }

    # Check foreground search
    foreground_result = None
    if needs_foreground_search(request.message):
      foreground_result = build_foreground_url(
        request.message
      )

    search_needed = needs_web_search(request.message)

    if foreground_result:
      url = foreground_result["url"]
      browser = foreground_result["browser"]
      description = foreground_result["description"]
      full_messages.insert(-1, Message(
        role="system",
        content=(
          f"[FOREGROUND BROWSER ACTION]\n"
          f"Open this URL for the user: {url}\n"
          f"Include exactly: "
          f"[UI_ACTION:open_url:{browser}:{url}]\n"
          f"Say: {description}"
        ),
        timestamp=""
      ))
      # Skip background search when foreground search is happening
      search_needed = False
    
    if search_needed:
        search_query_used = extract_search_query(request.message)
        try:
            search_results = await asyncio.wait_for(
                search_web(search_query_used, max_results=5),
                timeout=10.0
            )
            if search_results:
                search_context = (
                    f"\n\nWeb search results for '{search_query_used}':\n\n"
                )
                for i, r in enumerate(search_results, 1):
                    search_context += (
                        f"{i}. Source: {r.get('source', 'Unknown')}\n"
                        f"   {r['snippet'][:200]}\n\n"
                    )
                search_context += (
                    "\nInstructions: Summarize these results naturally. "
                    "Never show URLs. Cite sources by name only "
                    "(e.g. 'According to TechCrunch...'). "
                    "Be concise - 3-4 key points maximum."
                )
                if search_context:
                    search_context = search_context[:1500]
                full_messages.insert(-1, Message(
                    role="system",
                    content=search_context,
                    timestamp=""
                ))
                search_sources = search_results
                search_performed = True
                
                search_context_note = (
                    f"[Search results for: {search_query_used}]\n"
                )
                for r in search_sources[:3]:
                    search_context_note += (
                        f"- {r['title']} ({r.get('source', '')})\n"
                    )
                await save_message(
                    conversation_id=conversation_id,
                    role="system",
                    content=search_context_note
                )
        except (asyncio.TimeoutError, Exception) as e:
            print(f"Search error: {e}")

    try:
        # For file commands, use first available provider
        # No need for complex provider selection
        if is_file_cmd:
            providers_to_try = provider_manager.providers
        elif automation_results:
            providers_to_try = sorted(
                provider_manager.providers,
                key=lambda p: 0 if p.name == "openrouter" else 1 if p.name == "groq" else 2 if p.name == "ollama" else 3
            )
        else:
            providers_to_try = provider_manager.providers

        full_messages = trim_messages_to_budget(full_messages, max_tokens=4000)
        print(f"[CHAT] Attempting providers: {[p.name for p in providers_to_try]}")

        cascade = await run_cascade(
            full_messages, user_text=request.message, providers=providers_to_try
        )

        fallback_occurred = False
        failed_provider = None

        if cascade["status"] == "ok":
            response_text = cascade["response_text"]
            provider_used = cascade["provider_used"]
            model_used = cascade["model_used"]
            fallback_occurred = cascade.get("fallback_occurred", False)
            failed_provider = cascade.get("failed_provider")
            print(f"[CHAT] Successfully got response from {provider_used}" + (
                f" (after {failed_provider} failed)" if fallback_occurred else ""
            ))
        elif cascade["status"] == "asking":
            response_text = build_ask_message(cascade["failed_provider"], cascade.get("remaining", []))
            provider_used = "asking"
            model_used = "asking"
        elif cascade["status"] == "override_unavailable":
            response_text = build_override_unavailable_message(cascade["failed_provider"])
            provider_used = "override_unavailable"
            model_used = "unavailable"
        else:
            print(f"[CHAT] All providers failed")
            if provider_manager.is_unconfigured():
                raise Exception("NO_PROVIDER_CONFIGURED")
            raise Exception("All AI providers are currently unavailable")

    except Exception as e:
        print(f"[CHAT] Error: {e}")
        if str(e) == "NO_PROVIDER_CONFIGURED" or provider_manager.is_unconfigured():
            response_text = build_unconfigured_message()
        else:
            response_text = "I apologize, but all AI providers are currently unavailable."
        provider_used = "error"
        model_used = "error"
        fallback_occurred = False
        failed_provider = None

    response_text = enforce_destructive_confirmation(response_text)
    response_text = await detect_and_log_gap(response_text, request.message)
    response_text = briefing_prefix + response_text

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
        sources=search_sources,
        fallback_occurred=fallback_occurred,
        failed_provider=failed_provider
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

    # Daily briefing check - computed once up front so it applies
    # uniformly to whichever response path this request ends up taking
    # (pure automation, file command, or the general LLM streaming path).
    briefing_address_preference = await get_setting(
      "address_preference", settings.ADDRESS_PREFERENCE
    )
    briefing_prefix = await maybe_build_daily_briefing(briefing_address_preference)

    # Get relevant memories
    relevant_memories = await memory_manager.get_relevant_memories(request.message, limit=5)
    memory_context = ""
    if relevant_memories:
        memory_lines = [f"- {m['content']}" for m in relevant_memories]
        memory_context = "\n\nRelevant memories about Nithish:\n" + "\n".join(memory_lines)

    search_needed = needs_web_search(request.message)
    search_performed = False
    search_query_used = ""
    search_sources = []
    
    history = []
    search_context_accumulated = ""
    if request.conversation_id:
      history = await get_conversation_messages(
        conversation_id
      )
      system_msgs = [m for m in history if m.role == "system"]
      history = [m for m in history if m.role != "system"]
      if system_msgs:
          recent_system_msgs = system_msgs[-2:]
          search_context_accumulated = "\n\n" + "\n".join(m.content for m in recent_system_msgs)
          search_context_accumulated += "\n" + SEARCH_STRICT_INSTRUCTION
          
      # Universal history cap: Keep only the last 12 user/assistant turn-pairs (24 messages)
      history = history[-24:]
          
    active_provider = provider_manager.providers[0]
    available_providers = ", ".join(p.name.title() for p in provider_manager.providers)
    system_state = f"\n<SYSTEM_STATE>\nActive AI Brain (Provider): {active_provider.name.title()}\nActive Model: {active_provider.model}\nAvailable Brains: {available_providers}\n</SYSTEM_STATE>\n"

    personality_mode = await get_setting("personality_mode", settings.PERSONALITY_MODE)
    modifier = await get_setting("modifier", settings.MODIFIER)
    address_preference = await get_setting("address_preference", settings.ADDRESS_PREFERENCE)
    base_prompt = get_system_prompt(personality_mode, modifier, address_preference)

    system_message = Message(
      role="system",
      content=base_prompt + memory_context + search_context_accumulated + "\n" + UI_ACTION_INSTRUCTION + system_state,
      timestamp=""
    )
    
    new_user_message = Message(
      role="user",
      content=request.message,
      timestamp=""
    )
    
    # UI_ACTION reminder placed right before user message
    ui_reminder = Message(
      role="system",
      content=UI_ACTION_REMINDER,
      timestamp=""
    )
    
    # Build full message list and apply universal token-budget guard
    full_messages = (
      [system_message] + history + [ui_reminder] + [new_user_message]
    )
    full_messages = trim_messages_to_budget(full_messages, max_tokens=4000)
    
    await save_message(
      conversation_id=conversation_id,
      role="user",
      content=request.message
    )
    
    if search_needed:
        search_query_used = extract_search_query(request.message)

    # Check file system commands first
    is_file_cmd, file_action = is_file_system_command(request.message)
    automation_results = []

    if is_file_cmd:
        action = file_action["action"]
        path = file_action.get("path", "")
        description = file_action.get("description", "")
        requires_confirm = file_action.get("requires_confirmation", False)

        # Enhanced safety check
        is_destructive = is_destructive_action(request.message)

        if requires_confirm or is_destructive:
            fs_context = (
                f"[SAFETY CHECK REQUIRED]\n"
                f"This action is destructive and irreversible.\n"
                f"You MUST ask the user to confirm.\n"
                f"Say EXACTLY what will be deleted/affected.\n"
                f"Ask: 'Are you sure? Reply YES to confirm or NO to cancel.'\n"
                f"Include: [UI_ACTION:confirm_action:{action}:{path}]\n"
                f"DO NOT execute the action yet."
            )
        else:
            fs_context = (
                f"[FILE SYSTEM COMMAND DETECTED]\n"
                f"You MUST include this EXACT tag:\n"
                f"[UI_ACTION:{action}:{path}]\n"
                f"Acknowledge naturally. No graph actions."
            )

        # Use MINIMAL context for file commands
        # Skip conversation history, memory, search context - but still use
        # the real personality/modifier prompt (already fetched above),
        # not the hardcoded default, and no truncation (see /voice/input's
        # matching fix for why: truncating the prompt/capabilities silently
        # drops functionality rather than shortening tone).
        minimal_messages = [
            Message(
                role="system",
                content=get_system_prompt(personality_mode, modifier, address_preference),
                timestamp=""
            ),
            Message(
                role="system",
                content=fs_context,
                timestamp=""
            ),
            Message(
                role="user",
                content=request.message,
                timestamp=""
            )
        ]

        # Override full_messages with minimal context
        full_messages = minimal_messages
        search_needed = False
    else:
        # Check for automation intent
        if needs_automation(request.message) and settings.GROQ_API_KEY:
            automation_results = await generate_automation_command(
                request.message,
                settings.GROQ_API_KEY
            )

        if automation_results:
            automation_context = await get_automation_context_str(automation_results)
            full_messages.insert(-1, Message(
                role="system",
                content=automation_context,
                timestamp=""
            ))

    # Check foreground search
    foreground_result = None
    if needs_foreground_search(request.message):
      foreground_result = build_foreground_url(
        request.message
      )

    if foreground_result:
      url = foreground_result["url"]
      browser = foreground_result["browser"]
      description = foreground_result["description"]
      full_messages.insert(-1, Message(
        role="system",
        content=(
          f"[FOREGROUND BROWSER ACTION]\n"
          f"Open this URL for the user: {url}\n"
          f"Include exactly: "
          f"[UI_ACTION:open_url:{browser}:{url}]\n"
          f"Say: {description}"
        ),
        timestamp=""
      ))
      # Skip background search when
      # foreground search is happening
      search_needed = False

    # Check if this is a pure automation command that doesn't need AI (chat_stream)
    is_pure_automation = (
        len(automation_results) > 0 and
        all(r.get("action_type") in [
            "OPEN_APP", "OPEN_URL",
            "SYSTEM_CONTROL", "lock_screen"
        ] for r in automation_results)
    )

    if is_pure_automation:
        # Build response without AI
        descriptions = [
            r.get("description", "Done")
            for r in automation_results
        ]

        # Build UI action tags
        action_tags = ""
        for result in automation_results:
            action_type = result.get("action_type")
            command = result.get("command", "")
            browser = result.get("browser", "firefox")

            if action_type == "OPEN_APP":
                action_tags += f"[UI_ACTION:open_app:{command}]"
            elif action_type == "OPEN_URL":
                action_tags += f"[UI_ACTION:open_url:{browser}:{command}]"
            elif action_type == "SYSTEM_CONTROL":
                if command == "lock_screen":
                    action_tags += "[UI_ACTION:lock_screen]"

        # Build natural response
        if len(descriptions) == 1:
            response_text = f"{descriptions[0]}{_address_suffix(address_preference)}. {action_tags}"
        else:
            items = ", ".join(descriptions[:-1])
            items += f" and {descriptions[-1]}"
            response_text = f"Opening {items}{_address_suffix(address_preference)}. {action_tags}"

        response_text = briefing_prefix + response_text

        # Stream the response directly without AI
        async def generate_direct():
            yield json_module.dumps({
                "type": "meta",
                "conversation_id": conversation_id,
                "search_performed": False,
                "search_query": "",
                "sources": [],
                "provider": "direct",
                "model": "automation"
            }) + "\n"

            # Stream word by word
            for word in response_text.split():
                yield json_module.dumps({
                    "type": "token",
                    "content": word + " "
                }) + "\n"

            # Speak the response via TTS
            clean_response = response_text
            # Remove UI_ACTION tags before speaking
            import re
            clean_response = re.sub(
                r'\[UI_ACTION:[^\]]*\]', '', clean_response
            ).strip()

            if clean_response:
                import threading
                from ..voice.tts_engine import tts_engine
                def speak():
                    tts_engine.speak_sync(clean_response)
                t = threading.Thread(target=speak, daemon=True)
                t.start()

            # Save to DB
            await save_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text,
                provider_used="direct",
                model_used="automation"
            )

            yield json_module.dumps({
                "type": "done",
                "conversation_id": conversation_id,
                "full_response": response_text,
                "sources": [],
                "provider_used": "direct",
                "model_used": "automation"
            }) + "\n"

        return StreamingResponse(
            generate_direct(),
            media_type="application/x-ndjson"
        )

    async def generate():
      """Generator with disconnect detection to avoid wasted API credits."""
      nonlocal search_sources
      nonlocal full_messages
      try:
        # Send meta chunk first
        try:
          yield json_module.dumps({
            "type": "meta",
            "conversation_id": conversation_id,
            "search_performed": search_needed,
            "search_query": search_query_used,
            "sources": []
          }) + "\n"
        except Exception as meta_err:
          print(f"Meta chunk error: {meta_err}")

        # STEP 1: If search needed, do it FIRST
        if search_needed:
          yield json_module.dumps({
            "type": "search_started",
            "query": search_query_used
          }) + "\n"
          
          try:
            search_results = await asyncio.wait_for(
              search_web(search_query_used, max_results=5),
              timeout=10.0
            )
            if search_results:
              search_sources.extend(search_results)
              
              # Full snippets - not just titles
              search_context = (
                f"\n\nWeb search results for '{search_query_used}':\n\n"
              )
              for i, r in enumerate(search_results, 1):
                search_context += (
                  f"{i}. Source: {r.get('source', 'Unknown')}\n"
                  f"   {r['snippet'][:200]}\n\n"
                )
              search_context += (
                "\nInstructions: Summarize these results naturally. "
                "Never show URLs. Cite sources by name only "
                "(e.g. 'According to TechCrunch...'). "
                "Be concise - 3-4 key points maximum."
              )

              if search_context:
                search_context = search_context[:1500]
              
              # Inject BEFORE user message
              full_messages.insert(-1, Message(
                role="system",
                content=search_context,
                timestamp=""
              ))
              
              yield json_module.dumps({
                "type": "search_complete",
                "sources": [
                  {
                    "title": str(s.get("title", "")),
                    "url": str(s.get("url", "")),
                    "snippet": str(
                      s.get("snippet", "")[:200]
                    ),
                    "source": str(s.get("source", ""))
                  }
                  for s in search_results
                ]
              }) + "\n"
              
              # Save context note to db
              search_context_note = (
                f"[Search results for: {search_query_used}]\n"
              )
              for r in search_results[:3]:
                search_context_note += (
                  f"- {r['title']} ({r.get('source', '')})\n"
                )
              await save_message(
                conversation_id=conversation_id,
                role="system",
                content=search_context_note
              )
              
          except asyncio.TimeoutError:
            print(f"Search timed out: {search_query_used}")
            yield json_module.dumps({
              "type": "search_timeout",
              "message": "Web search timed out after 10s"
            }) + "\n"
          except Exception as e:
            print(f"Search error: {e}")

        # STEP 2: Stream AI with full context
        full_response_parts = []
        provider_used_name = "unknown"
        model_used_name = "unknown"
        stream_started = False
        fallback_occurred = False
        failed_provider_name = None

        try:
          # For file commands, use first available provider
          # No need for complex provider selection
          if is_file_cmd:
            providers_to_try = provider_manager.providers
          elif automation_results:
            providers_to_try = sorted(
              provider_manager.providers,
              key=lambda p: 0 if p.name == "openrouter" else 1 if p.name == "groq" else 2 if p.name == "ollama" else 3
            )
          else:
            providers_to_try = provider_manager.providers

          full_messages = trim_messages_to_budget(full_messages, max_tokens=4000)

          # Provider override / ask-before-fallback settings - same rules
          # the non-streaming /chat and /voice/input endpoints apply, see
          # providers/fallback.py.
          override, fallback_mode = await fallback_module.get_provider_settings()
          one_shot_provider = await fallback_module.consume_awaiting_choice(request.message)
          if one_shot_provider:
            override = one_shot_provider

          asking_message = None
          override_unavailable_provider = None

          if override:
            matched = next((p for p in providers_to_try if p.name == override), None)
            if matched is None or not await matched.is_available():
              override_unavailable_provider = override
              providers_to_try = []
            else:
              providers_to_try = [matched]

          print(f"[STREAM] Attempting providers: {[p.name for p in providers_to_try]}")

          failed_providers: list[str] = []

          for provider in providers_to_try:
            if not await provider.is_available():
                print(f"[STREAM] Provider {provider.name} not available, skipping")
                failed_providers.append(provider.name)
                if fallback_mode == "ask" and not override:
                  await set_setting("awaiting_provider_choice", "true")
                  asking_message = build_ask_message(
                    provider.name,
                    [p.name for p in providers_to_try if p.name != provider.name]
                  )
                  break
                continue

            provider_used_name = provider.name
            model_used_name = provider.model
            print(f"[STREAM] Using provider: {provider.name}, model: {provider.model}")

            try:
              async for token in provider.stream(full_messages):
                full_response_parts.append(token)
                stream_started = True
                yield json_module.dumps({
                  "type": "token",
                  "content": token
                }) + "\n"

              # Stream completed successfully
              if failed_providers:
                fallback_occurred = True
                failed_provider_name = failed_providers[0]
              print(f"[STREAM] Successfully completed with {provider.name}")
              break
            except asyncio.CancelledError:
              # Client disconnected - stop generating tokens to save API credits
              print(f"[STREAM] Client disconnected, stopping generation (saved {len(full_response_parts)} tokens)")
              break
            except Exception as stream_err:
              print(f"[STREAM] Error with {provider.name}: {stream_err}")
              if stream_started:
                # Already yielded tokens - complete with what we have
                print(f"[STREAM] Completing with partial response from {provider.name}")
                break
              failed_providers.append(provider.name)
              if fallback_mode == "ask" and not override:
                await set_setting("awaiting_provider_choice", "true")
                asking_message = build_ask_message(
                  provider.name,
                  [p.name for p in providers_to_try if p.name != provider.name]
                )
                break
              # No tokens sent yet - try next provider
              print(f"[STREAM] Falling back to next provider")
              full_response_parts = []  # Reset
              continue

          if override_unavailable_provider:
            error_msg = build_override_unavailable_message(override_unavailable_provider)
            full_response_parts = [error_msg]
            provider_used_name = "override_unavailable"
            model_used_name = "unavailable"
            yield json_module.dumps({
              "type": "token",
              "content": error_msg
            }) + "\n"
          elif asking_message:
            full_response_parts = [asking_message]
            provider_used_name = "asking"
            model_used_name = "asking"
            yield json_module.dumps({
              "type": "token",
              "content": asking_message
            }) + "\n"
          # If no provider succeeded at all
          elif not stream_started and not full_response_parts:
            print(f"[STREAM] All providers failed, sending error token")
            if provider_manager.is_unconfigured():
              error_msg = build_unconfigured_message()
            else:
              error_msg = "I apologize, but all AI providers are currently unavailable."
            full_response_parts = [error_msg]
            yield json_module.dumps({
              "type": "token",
              "content": error_msg
            }) + "\n"

        except asyncio.CancelledError:
          print(f"[STREAM] Request cancelled by client during streaming")
          # Don't re-raise - let cleanup happen gracefully
          complete_response = "".join(full_response_parts) if full_response_parts else ""
        except Exception as e:
          print(f"[STREAM] Fatal streaming error: {e}")
          import traceback
          traceback.print_exc()

        # STEP 3: Save and send done
        complete_response = "".join(full_response_parts)
        complete_response = enforce_destructive_confirmation(complete_response)
        
        new_response = await detect_and_log_gap(complete_response, request.message)
        if len(new_response) > len(complete_response):
            gap_note = new_response[len(complete_response):]
            yield json_module.dumps({
                "type": "token",
                "content": gap_note
            }) + "\n"
            complete_response = new_response
        # Prepended here rather than seeded into full_response_parts up
        # front - the provider-fallback path above resets
        # full_response_parts to [] on retry, which would silently wipe a
        # pre-seeded briefing. This point is reached exactly once
        # regardless of how many providers were tried.
        complete_response = briefing_prefix + complete_response

        if complete_response:
          try:
            await save_message(
              conversation_id=conversation_id,
              role="assistant",
              content=complete_response,
              provider_used=provider_used_name,
              model_used=model_used_name
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

          # Speak response via TTS (non-blocking)
          try:
            from ..voice.tts_engine import tts_engine
            import re

            async def speak_and_broadcast():
              # Strip UI_ACTION tags before speaking
              clean = re.sub(
                r'\[UI_ACTION:[^\]]*\]',
                '', complete_response
              ).strip()

              # Strip markdown formatting for cleaner TTS
              clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)  # Bold
              clean = re.sub(r'\*(.+?)\*', r'\1', clean)  # Italic
              clean = re.sub(r'#{1,6}\s', '', clean)  # Headers
              clean = re.sub(r'`(.+?)`', r'\1', clean)  # Inline code
              clean = re.sub(r'```[\s\S]*?```', '', clean)  # Code blocks
              clean = clean.strip()

              if fallback_occurred and failed_provider_name:
                # Natural spoken note about the switch, prepended to the
                # actual answer rather than a separate interruption.
                clean = build_fallback_note(failed_provider_name, provider_used_name) + clean

              if clean and len(clean) > 10:
                # Broadcast "speaking" only once audio actually starts
                # playing, via tts_engine's on_speech_start callback (fires
                # off the TTS thread, so hop back to the event loop with
                # call_soon_threadsafe to schedule the broadcast coroutine).
                loop = asyncio.get_event_loop()

                def _on_speech_start():
                  loop.call_soon_threadsafe(
                    asyncio.create_task,
                    broadcast_voice_event({
                      "type": "voice_status",
                      "status": "speaking"
                    })
                  )

                # Speak in separate thread (blocking call)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                  await loop.run_in_executor(
                    executor,
                    tts_engine.speak_sync,
                    clean,
                    _on_speech_start
                  )

                # Broadcast idle status after speaking
                await broadcast_voice_event({
                  "type": "voice_status",
                  "status": "idle"
                })

            # Schedule TTS as background task
            asyncio.create_task(speak_and_broadcast())
          except Exception as e:
            print(f"TTS speak error: {e}")

        # Send done chunk
        yield json_module.dumps({
          "type": "done",
          "conversation_id": conversation_id,
          "full_response": complete_response,
          "provider_used": provider_used_name,
          "model_used": model_used_name,
          "fallback_occurred": fallback_occurred,
          "failed_provider": failed_provider_name,
          "sources": [
            {
              "title": str(s.get("title", "")),
              "url": str(s.get("url", "")),
              "snippet": str(s.get("snippet", "")[:200]),
              "source": str(s.get("source", ""))
            }
            for s in search_sources
          ]
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

    try:
        from ..voice.tts_engine import tts_engine
        tts_ready = tts_engine.kokoro_ready.is_set()
    except Exception:
        tts_ready = False

    voice_ready = (
        tts_ready
        and voice_manager.whisper_ready.is_set()
        and voice_manager.wake_word_ready.is_set()
    )

    return HealthResponse(
        status="online",
        version=settings.VERSION,
        providers=statuses,
        voice_ready=voice_ready
    )

@router.get("/conversation/{conversation_id}", response_model=List[Message])
async def get_conversation_endpoint(conversation_id: str):
    messages = await get_conversation_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Filter out system messages so they don't appear in the frontend UI
    return [msg for msg in messages if msg.role != "system"]

@router.delete("/conversation/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str, pin: str = ""):
    # Same server-side check as DELETE /memories/{id} - same stored
    # conversation_delete_pin setting, same comparison - not a client-side
    # comparison the frontend could be tricked into skipping.
    stored_pin = await get_setting("conversation_delete_pin", settings.CONVERSATION_DELETE_PIN)
    if str(pin).strip() != stored_pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")

    deleted = await delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}

class UpdateTitleRequest(BaseModel):
    title: str

@router.put("/conversation/{conversation_id}/title")
async def update_conversation_title_endpoint(conversation_id: str, request: UpdateTitleRequest):
    try:
        await update_conversation_title(conversation_id, request.title)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "updated", "conversation_id": conversation_id, "title": request.title}

@router.get("/providers")
async def get_providers_endpoint():
    return await provider_manager.get_status()

class SwitchProviderRequest(BaseModel):
    provider: str
    model: str

@router.post("/provider/switch")
async def switch_provider_endpoint(request: SwitchProviderRequest):
    provider_manager.set_active_provider(request.provider, request.model)

    # Persist as the PREFERRED provider (soft: just the cascade's first
    # choice on next restart) - distinct from provider_override (hard
    # lock, no fallback). Only recorded for a name the manager actually
    # recognizes, so a bad/unknown value can't get "restored" into a
    # silent no-op reorder on the next startup - matches how
    # provider_override validates in update_settings_endpoint above.
    if request.provider in fallback_module.VALID_PROVIDERS:
        await set_setting("preferred_provider", request.provider)
        await set_setting("preferred_model", request.model)

    return {"status": "success", "provider": request.provider, "model": request.model}

@router.get("/memories", response_model=List[Memory])
async def get_memories_endpoint():
    memories = await memory_manager.get_all_memories(limit=100)
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

@router.put("/memories/{memory_id}", response_model=Memory)
async def update_memory_endpoint(memory_id: str, request: UpdateMemoryRequest):
    updated = await memory_manager.update_memory(
        memory_id,
        content=request.content,
        category=request.category,
        importance=request.importance
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found")
    return updated

@router.delete("/memories/{memory_id}")
async def delete_memory_endpoint(memory_id: str, pin: str = ""):
    # Same server-side check as /settings/verify-pin - same stored
    # conversation_delete_pin setting, same comparison - not a separate
    # memory-specific PIN and not a client-side comparison the frontend
    # could be tricked into skipping.
    stored_pin = await get_setting("conversation_delete_pin", settings.CONVERSATION_DELETE_PIN)
    if str(pin).strip() != stored_pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")

    deleted = await memory_manager.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": deleted}

@router.get("/memories/search", response_model=List[Memory])
async def search_memories_endpoint(q: str):
    results = await memory_manager.get_relevant_memories(q, limit=50)
    return results

@router.get("/conversations")
async def get_conversations_endpoint():
    return await get_conversations(limit=200)

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
async def set_openrouter_key(request: dict):
  key = request.get("api_key", "")
  import os
  from dotenv import set_key
  os.environ["OPENROUTER_API_KEY"] = key
  env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
  set_key(env_path, "OPENROUTER_API_KEY", key)
  from ..core.config import settings
  settings.OPENROUTER_API_KEY = key
  return {"status": "updated"}

@router.post("/config/groq-key")
async def set_groq_key(request: dict):
  key = request.get("api_key", "")
  import os
  from dotenv import set_key
  os.environ["GROQ_API_KEY"] = key
  env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
  set_key(env_path, "GROQ_API_KEY", key)
  from ..core.config import settings
  settings.GROQ_API_KEY = key
  return {"status": "updated"}

@router.post("/config/gemini-key")
async def set_gemini_key(request: dict):
  key = request.get("api_key", "")
  import os
  from dotenv import set_key
  os.environ["GEMINI_API_KEY"] = key
  env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
  set_key(env_path, "GEMINI_API_KEY", key)
  from ..core.config import settings
  settings.GEMINI_API_KEY = key
  return {"status": "updated"}

@router.get("/plugins")
async def get_plugins():
    from ..plugins.registry import registry
    result = []
    for p in registry.list_plugins():
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "is_configured": registry.is_configured(p.id)
        })
    return result

@router.delete("/plugins/{plugin_id}/credentials")
async def delete_plugin_credentials(plugin_id: str):
    """Disconnect a plugin by clearing its stored credentials.

    Resolves the credential namespace first - gmail and google_calendar
    both store under "google". Passing the raw plugin_id to the store (as
    this used to) looked for keys that were never there, deleted nothing,
    and still returned {"status": "ok"}, so Disconnect appeared to work
    while the OAuth tokens stayed on disk.

    Clearing a shared namespace disconnects every plugin using it, which
    mirrors how connecting already works: one Google consent screen
    issues the tokens for both, so there is no way to revoke one without
    the other. `also_disconnected` names the rest so the UI can say so.
    """
    from ..plugins.credential_store import delete_credential, list_credential_keys
    from ..plugins.registry import registry

    namespace = registry.resolve_namespace(plugin_id)
    if namespace is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown plugin '{plugin_id}'"
        )

    keys = list_credential_keys(namespace)
    for k in keys:
        delete_credential(namespace, k)

    affected = registry.plugins_sharing_namespace(namespace)

    # deleted_keys is reported so a silent no-op is visible to the caller
    # rather than indistinguishable from a real disconnect.
    return {
        "status": "ok",
        "namespace": namespace,
        "deleted_keys": len(keys),
        "also_disconnected": [p for p in affected if p != plugin_id],
    }

# --- Google OAuth Endpoints ---
@router.get("/plugins/google/auth-url")
async def get_google_auth_url():
    from ..plugins.google_auth import get_authorization_url
    return {"url": get_authorization_url()}

@router.get("/plugins/google/callback")
async def google_auth_callback(code: str):
    from ..plugins.google_auth import handle_callback
    from fastapi.responses import HTMLResponse
    handle_callback(code)
    return HTMLResponse("<script>window.close();</script><h1>Authentication successful! You can close this tab.</h1>")

# --- Gmail Plugin Endpoints ---
def _check_plugin(plugin_id: str):
    from ..plugins.registry import registry
    from fastapi import HTTPException
    if not registry.is_configured(plugin_id):
        raise HTTPException(status_code=503, detail=f"Plugin {plugin_id} is not configured.")

@router.get("/plugins/gmail/unread")
async def get_unread_emails():
    _check_plugin("gmail")
    from ..plugins.gmail_plugin import get_unread_emails
    return get_unread_emails()

from pydantic import BaseModel
class GmailSearchRequest(BaseModel):
    query: str
class GmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/plugins/gmail/search")
async def search_emails(req: GmailSearchRequest):
    _check_plugin("gmail")
    from ..plugins.gmail_plugin import search_emails
    return search_emails(req.query)

@router.post("/plugins/gmail/send")
async def send_email(req: GmailSendRequest):
    _check_plugin("gmail")
    from ..plugins.gmail_plugin import send_email
    send_email(req.to, req.subject, req.body)
    return {"status": "ok"}

# --- Google Calendar Plugin Endpoints ---
class CalendarCreateRequest(BaseModel):
    title: str
    start: str
    end: str
    description: str = ""

@router.get("/plugins/calendar/today")
async def get_calendar_today():
    _check_plugin("google_calendar")
    from ..plugins.calendar_plugin import get_todays_events
    return get_todays_events()

@router.get("/plugins/calendar/upcoming")
async def get_calendar_upcoming():
    _check_plugin("google_calendar")
    from ..plugins.calendar_plugin import get_upcoming_events
    return get_upcoming_events()

@router.post("/plugins/calendar/create")
async def create_calendar_event(req: CalendarCreateRequest):
    _check_plugin("google_calendar")
    from ..plugins.calendar_plugin import create_event
    from fastapi import HTTPException
    import httpx
    
    try:
        create_event(req.title, req.start, req.end, req.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        # e.response.text gives the actual Google API error body if available
        raise HTTPException(status_code=503, detail=f"Calendar API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "ok"}

# --- GitHub Plugin Endpoints ---
class GithubConnectRequest(BaseModel):
    token: str

@router.post("/plugins/github/connect")
async def connect_github(req: GithubConnectRequest):
    from ..plugins.github_plugin import validate_and_store_token
    from fastapi import HTTPException
    success = validate_and_store_token(req.token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid GitHub token")
    return {"status": "connected"}

@router.get("/plugins/github/repos")
async def github_repos():
    _check_plugin("github")
    from ..plugins.github_plugin import list_repos
    return list_repos()

@router.get("/plugins/github/issues")
async def github_issues(repo: str, state: str = "open"):
    _check_plugin("github")
    from ..plugins.github_plugin import list_issues
    return list_issues(repo, state)

@router.get("/plugins/github/search/issues")
async def github_search_issues(query: str):
    _check_plugin("github")
    from ..plugins.github_plugin import search_issues
    return search_issues(query)

class GithubIssueRequest(BaseModel):
    repo: str
    title: str
    body: str = ""

@router.post("/plugins/github/issues")
async def github_create_issue(req: GithubIssueRequest):
    _check_plugin("github")
    from ..plugins.github_plugin import create_issue
    create_issue(req.repo, req.title, req.body)
    return {"status": "ok"}

@router.get("/plugins/github/pulls")
async def github_pulls(repo: str, state: str = "open"):
    _check_plugin("github")
    from ..plugins.github_plugin import list_pull_requests
    return list_pull_requests(repo, state)

@router.get("/plugins/github/pulls/status")
async def github_pr_status(repo: str, number: int):
    _check_plugin("github")
    from ..plugins.github_plugin import get_pr_status
    return get_pr_status(repo, number)

@router.get("/plugins/github/search/code")
async def github_search_code(query: str, repo: str = None):
    _check_plugin("github")
    from ..plugins.github_plugin import search_code
    return search_code(query, repo)

# --- Weather Plugin Endpoints ---
@router.get("/plugins/weather/current")
async def get_weather_current(location: str | None = None):
    _check_plugin("weather")
    from ..core.config import settings
    from ..plugins.weather_plugin import get_current_weather
    loc = location if location else settings.WEATHER_DEFAULT_LOCATION
    return get_current_weather(loc)

@router.get("/plugins/weather/forecast")
async def get_weather_forecast(location: str | None = None, days: int = 3):
    _check_plugin("weather")
    from ..core.config import settings
    from ..plugins.weather_plugin import get_forecast
    loc = location if location else settings.WEATHER_DEFAULT_LOCATION
    return get_forecast(loc, days)

@router.get("/capabilities")
async def get_capabilities():
    from ..core.capability_registry import get_all_capabilities
    caps = get_all_capabilities()
    return [c.dict() for c in caps]

@router.get("/gaps")
async def get_gaps():
    from ..core.config import settings
    import aiosqlite
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT gap_id, user_request, detected_intent, gap_reason, timestamp, resolved FROM gap_log ORDER BY timestamp DESC LIMIT 50"
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching gaps: {e}")
        return []

@router.post("/gaps/{gap_id}/resolve")
async def resolve_gap(gap_id: str):
    from ..core.config import settings
    import aiosqlite
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "UPDATE gap_log SET resolved = 1 WHERE gap_id = ?",
                (gap_id,)
            )
            await db.commit()
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
