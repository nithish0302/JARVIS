import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json as json_module
from typing import List
import aiosqlite

from ..core.models import ChatRequest, ChatResponse, HealthResponse, Message, Memory, CreateMemoryRequest
from ..core.config import settings
from ..providers.manager import provider_manager
from ..memory.conversation import save_message, get_conversation_messages, delete_conversation, get_conversations, update_conversation_title
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

You are not a generic chatbot. You are JARVIS — act like it.
"""

UI_ACTION_REMINDER = (
    "Remember: You can use [UI_ACTION:command] "
    "tags to control the interface. Available: "
    "graph_open_hub:Skills/Tools/Files/Notes/Models, "
    "chat_mode_on, chat_mode_off, graph_collapse, "
    "conversations_open, switch_provider:name, "
    "new_chat[:title], rename_chat:title, delete_conversation:title, open_chat:title"
)

UI_ACTION_INSTRUCTION = """
<SYSTEM_CAPABILITIES>
You can control the JARVIS interface by including special action tags in your response.

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
[UI_ACTION:new_chat] - Start a new chat session / clear conversation
[UI_ACTION:new_chat:Title] - Start a new chat session and pre-set its title
[UI_ACTION:open_chat:Title] - Open an existing past chat by its title
[UI_ACTION:rename_chat:Title] - Rename the current conversation to the given title
[UI_ACTION:delete_conversation:Title] - Delete a past conversation by searching its title

CRITICAL RULES FOR UI ACTIONS:
- NEVER use a UI action unless the user EXPLICITLY asks you to perform that specific action.
- If you are answering a question or providing search results, DO NOT include any UI actions!
- YOU MUST include the EXACT bracketed tag (e.g. [UI_ACTION:chat_mode_on]) when requested.
- Put action tags at the END of your response
- Never show the raw tag text to the user
- Multiple actions can be included if needed
- If the user asks to open "memory index", "chat history", "list the chats", or "past chats", use [UI_ACTION:conversations_open]
- If the user asks to "start a new chat", "open a new chat", or "clear the chat", use [UI_ACTION:new_chat]
- If the user asks to start a new chat AND specifies a title, use [UI_ACTION:new_chat:Title]
- If the user asks to open an existing old/past chat by name, use [UI_ACTION:open_chat:Title]
- If the user asks to name/rename the CURRENT chat, use [UI_ACTION:rename_chat:Title]
- If the user asks to delete a conversation, use [UI_ACTION:delete_conversation:Title]

Examples:
- User: "open skills" -> Assistant: "Opening skills now. [UI_ACTION:graph_open_hub:Skills]"
- User: "start a new chat" -> Assistant: "Starting a fresh conversation. [UI_ACTION:new_chat]"
- User: "open a new chat and name it ai news" -> Assistant: "Starting a new chat titled 'ai news'. [UI_ACTION:new_chat:ai news]"
- User: "open ai news" or "open the ai news chat" -> Assistant: "Opening conversation 'ai news'. [UI_ACTION:open_chat:ai news]"
- User: "name this chat as the 3050" -> Assistant: "Renaming chat to '3050'. [UI_ACTION:rename_chat:3050]"
- User: "delete the 3050 conversation" -> Assistant: "Initiating deletion for the 3050 conversation. [UI_ACTION:delete_conversation:3050]"
- User: "switch to chat mode" -> Assistant: "Switching to chat mode. [UI_ACTION:chat_mode_on]"
- User: "close the chat mode" -> Assistant: "Switching back to graph mode. [UI_ACTION:chat_mode_off]"
- User: "collapse the graph" -> Assistant: "Collapsing the graph. [UI_ACTION:graph_collapse]"
</SYSTEM_CAPABILITIES>
"""
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

COMMAND_GENERATION_PROMPT = """You are a Windows 
automation expert for JARVIS.

The user wants to do something on their Windows PC.
Generate the exact PowerShell command to do it.

User request: "{request}"

Rules:
1. Return ONLY a JSON object or JSON ARRAY, nothing else
2. Format:
{{
  "action_type": "OPEN_APP|OPEN_URL|SYSTEM_QUERY|FILE_OP|SYSTEM_CONTROL|UNSAFE",
  "command": "the powershell command, app name, or url",
  "description": "what this will do in plain English",
  "requires_confirmation": true/false,
  "display_output": true/false
}}

If the user wants to open MULTIPLE apps,
return a JSON ARRAY:
[
  {{"action_type":"OPEN_APP","command":"Firefox","description":"Opening Firefox","requires_confirmation":false,"display_output":false}},
  {{"action_type":"OPEN_APP","command":"Code","description":"Opening VS Code","requires_confirmation":false,"display_output":false}}
]

CRITICAL DEDUPLICATION RULE:
If you are opening a URL in a browser,
do NOT also generate a separate OPEN_APP
action for that same browser.

WRONG (creates 2 windows):
[
  {{"action_type":"OPEN_APP","command":"Firefox"}},
  {{"action_type":"OPEN_URL","command":"https://youtube.com","browser":"firefox"}}
]

CORRECT (opens Firefox once with YouTube):
[
  {{"action_type":"OPEN_URL","command":"https://youtube.com","browser":"firefox","description":"Opening YouTube in Firefox","requires_confirmation":false,"display_output":false}}
]

Rule: OPEN_URL already opens the browser.
Never combine OPEN_APP + OPEN_URL for the same browser.

More examples:
'open firefox and go to youtube'
→ [{{"action_type":"OPEN_URL","command":"https://youtube.com","browser":"firefox"}}]

'open firefox and search cats'
→ [{{"action_type":"OPEN_URL","command":"https://google.com/search?q=cats","browser":"firefox"}}]

'open firefox and search youtube for tamil songs'
→ [{{"action_type":"OPEN_URL","command":"https://youtube.com/results?search_query=tamil+songs","browser":"firefox"}}]

'open firefox and notepad'
→ [
    {{"action_type":"OPEN_URL","command":"https://www.google.com","browser":"firefox"}},
    {{"action_type":"OPEN_APP","command":"notepad"}}
  ]
(Firefox opens with Google, notepad opens separately)

CRITICAL: For locking the screen, ALWAYS return:
{{"action_type":"SYSTEM_CONTROL","command":"lock_screen","description":"Locking Windows screen","requires_confirmation":false,"display_output":false}}
NEVER generate a PowerShell script to lock screen.

For disk space queries use this exact command:
Get-PSDrive C | Select-Object @{{N='Used GB';E={{[math]::Round($_.Used/1GB,1)}}}},@{{N='Free GB';E={{[math]::Round($_.Free/1GB,1)}}}},@{{N='Total GB';E={{[math]::Round(($_.Used+$_.Free)/1GB,1)}}}},@{{N='Used %';E={{[math]::Round($_.Used/($_.Used+$_.Free)*100,1)}}}} | Format-Table -AutoSize

User's preferred browsers:
1. Firefox (primary - use by default)
2. Edge (secondary)
When opening any URL without browser specified,
always use Firefox.

Examples:
Request: "open chrome"
{{"action_type":"OPEN_APP","command":"Chrome","description":"Opening Google Chrome","requires_confirmation":false,"display_output":false}}

Request: "open youtube in firefox"
{{"action_type":"OPEN_URL","command":"https://youtube.com","browser":"firefox","description":"Opening YouTube in Firefox","requires_confirmation":false,"display_output":false}}

Request: "search cats on youtube"
{{"action_type":"OPEN_URL","command":"https://youtube.com/results?search_query=cats","browser":"firefox","description":"Searching cats on YouTube","requires_confirmation":false,"display_output":false}}

Request: "open gmail"
{{"action_type":"OPEN_URL","command":"https://gmail.com","browser":"firefox","description":"Opening Gmail in Firefox","requires_confirmation":false,"display_output":false}}

Request: "what processes are using most CPU"
{{"action_type":"SYSTEM_QUERY","command":"Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name,CPU | Format-Table","description":"Showing top 5 CPU-consuming processes","requires_confirmation":false,"display_output":true}}

Request: "delete all files in Downloads"
{{"action_type":"FILE_OP","command":"Remove-Item $HOME\\Downloads\\* -Recurse","description":"This will permanently delete ALL files in Downloads","requires_confirmation":true,"display_output":false}}

Request: "lock my screen"
{{"action_type":"SYSTEM_CONTROL","command":"lock_screen","description":"Locking your Windows screen","requires_confirmation":false,"display_output":false}}

Request: "open google and search JARVIS AI"
{{"action_type":"OPEN_URL","command":"https://google.com/search?q=JARVIS+AI","browser":"firefox","description":"Searching JARVIS AI on Google","requires_confirmation":false,"display_output":false}}

Request: "open store and search forza 6"
{{"action_type":"OPEN_URL","command":"ms-windows-store://search?query=forza+6","browser":"default","description":"Opening Microsoft Store and searching for Forza 6","requires_confirmation":false,"display_output":false}}

Request: "open youtube and search tamil songs"
{{"action_type":"OPEN_URL","command":"https://youtube.com/results?search_query=tamil+songs","browser":"firefox","description":"Searching Tamil songs on YouTube","requires_confirmation":false,"display_output":false}}

Request: "open amazon and search laptop"
{{"action_type":"OPEN_URL","command":"https://amazon.in/s?k=laptop","browser":"firefox","description":"Searching laptop on Amazon","requires_confirmation":false,"display_output":false}}

Common searchable URLs:
- YouTube: https://youtube.com/results?search_query=QUERY
- Google: https://google.com/search?q=QUERY
- Amazon India: https://amazon.in/s?k=QUERY
- Microsoft Store: ms-windows-store://search?query=QUERY
- GitHub: https://github.com/search?q=QUERY
- Stack Overflow: https://stackoverflow.com/search?q=QUERY

Replace spaces with + in QUERY.
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
      
      query_lower = query.lower()
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
    automation_context = (
        f"[TASK] Include these exact tags in your "
        f"response and describe the action naturally:\n"
    )
    for result in automation_results:
        action_type = result.get("action_type", "")
        command = result.get("command", "")
        browser = result.get("browser", "firefox")
        description = result.get("description", "")
        requires_confirm = result.get("requires_confirmation", False)

        if action_type == "OPEN_APP":
            automation_context += (
                f"[UI_ACTION:open_app:{command}] "
                f"({description})\n"
            )
        elif action_type == "OPEN_URL":
            automation_context += (
                f"[UI_ACTION:open_url:{browser}:{command}] "
                f"({description})\n"
            )
        elif action_type == "SYSTEM_CONTROL" and command == "lock_screen":
            automation_context += (
                f"[UI_ACTION:lock_screen] "
                f"(Lock the Windows screen)\n"
            )
        elif action_type == "SYSTEM_QUERY":
            automation_context += (
                f"[UI_ACTION:run_powershell:{command}] "
                f"(Run system query)\n"
            )
        elif requires_confirm:
            automation_context += (
                f"[UI_ACTION:confirm_action:{command}] "
                f"(Ask user to confirm: {description})\n"
            )
        elif action_type in ("SYSTEM_CONTROL", "FILE_OP") and not requires_confirm:
            automation_context += (
                f"[UI_ACTION:run_powershell:{command}] "
                f"({description})\n"
            )
    return automation_context[:300]


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
        "content": COMMAND_GENERATION_PROMPT.format(
          request=message
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
            search_context_accumulated = "\n\n" + "\n".join(m.content for m in system_msgs)
            search_context_accumulated += "\n" + SEARCH_STRICT_INSTRUCTION
            
    active_provider = provider_manager.providers[0]
    available_providers = ", ".join(p.name.title() for p in provider_manager.providers)
    system_state = f"\n<SYSTEM_STATE>\nActive AI Brain (Provider): {active_provider.name.title()}\nActive Model: {active_provider.model}\nAvailable Brains: {available_providers}\n</SYSTEM_STATE>\nIf the user asks to switch models or brains to an available brain, you MUST use [UI_ACTION:switch_provider:provider_name] (e.g. [UI_ACTION:switch_provider:gemini] or [UI_ACTION:switch_provider:groq]).\n"
            
    system_message = Message(
        role="system",
        content=JARVIS_SYSTEM_PROMPT + memory_context + search_context_accumulated + "\n" + UI_ACTION_INSTRUCTION + system_state,
        timestamp=""
    )
        
    # Create new user message
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
    
    # Build full message list
    full_messages = [system_message] + history + [ui_reminder] + [new_user_message]
    
    # Save user message to DB
    await save_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    
    # Check for automation intent
    automation_results = []
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
                    f"\n\nCurrent web search results for "
                    f"'{search_query_used}':\n\n"
                )
                for i, r in enumerate(search_results, 1):
                    search_context += (
                        f"{i}. {r['title']}\n"
                        f"   {r['snippet']}\n"
                        f"   URL: {r['url']}\n\n"
                    )
                search_context += (
                    "Use ONLY these results. Cite sources."
                )
                if search_context:
                    search_context = search_context[:1000]
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
        if automation_results:
            providers_to_try = sorted(
                provider_manager.providers,
                key=lambda p: 0 if p.name == "openrouter" else 1 if p.name == "groq" else 2 if p.name == "ollama" else 3
            )
        else:
            providers_to_try = provider_manager.providers

        response_text = ""
        for provider in providers_to_try:
            if not await provider.is_available():
                continue
            try:
                response_text = await provider.chat(full_messages)
                provider_used = provider.name
                model_used = provider.model
                break
            except Exception:
                continue
        if not response_text:
            raise Exception("All providers failed")
    except Exception as e:
        response_text = "I encountered an error."
        provider_used = "error"
        model_used = "error"
    
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
          search_context_accumulated = "\n\n" + "\n".join(m.content for m in system_msgs)
          search_context_accumulated += "\n" + SEARCH_STRICT_INSTRUCTION
          
    active_provider = provider_manager.providers[0]
    available_providers = ", ".join(p.name.title() for p in provider_manager.providers)
    system_state = f"\n<SYSTEM_STATE>\nActive AI Brain (Provider): {active_provider.name.title()}\nActive Model: {active_provider.model}\nAvailable Brains: {available_providers}\n</SYSTEM_STATE>\nIf the user asks to switch models or brains to an available brain, you MUST use [UI_ACTION:switch_provider:provider_name] (e.g. [UI_ACTION:switch_provider:gemini] or [UI_ACTION:switch_provider:groq]).\n"

    system_message = Message(
      role="system",
      content=JARVIS_SYSTEM_PROMPT + memory_context + search_context_accumulated + "\n" + UI_ACTION_INSTRUCTION + system_state,
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
    
    full_messages = (
      [system_message] + history + [ui_reminder] + [new_user_message]
    )
    
    await save_message(
      conversation_id=conversation_id,
      role="user",
      content=request.message
    )
    
    if search_needed:
        search_query_used = extract_search_query(request.message)

    # Check for automation intent
    automation_results = []
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

    async def generate():
      nonlocal search_sources
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
                f"\n\nCurrent web search results for "
                f"'{search_query_used}':\n\n"
              )
              for i, r in enumerate(search_results, 1):
                search_context += (
                  f"{i}. {r['title']}\n"
                  f"   {r['snippet']}\n"
                  f"   URL: {r['url']}\n\n"
                )
              search_context += (
                "Use ONLY the above search results to "
                "answer. Cite sources by website name. "
                "Do NOT add facts from training data."
              )
              
              if search_context:
                search_context = search_context[:1000]
              
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

        try:
          if automation_results:
            providers_to_try = sorted(
              provider_manager.providers,
              key=lambda p: 0 if p.name == "openrouter" else 1 if p.name == "groq" else 2 if p.name == "ollama" else 3
            )
          else:
            providers_to_try = provider_manager.providers

          for provider in providers_to_try:
            if not await provider.is_available():
                continue

            provider_used_name = provider.name
            model_used_name = provider.model

            try:
              async for token in provider.stream(full_messages):
                full_response_parts.append(token)
                yield json_module.dumps({
                  "type": "token",
                  "content": token
                }) + "\n"
              
              # Stream completed successfully
              break
            except Exception as stream_err:
              print(f"Stream error for {provider.name}: {stream_err}")
              if full_response_parts:
                # Already yielded parts, can't cleanly fallback
                break
              # Fallback to the next provider
              continue
        except Exception as e:
          print(f"Streaming failed across providers: {e}")

        # STEP 3: Save and send done
        complete_response = "".join(full_response_parts)
        
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

        # Send done chunk
        yield json_module.dumps({
          "type": "done",
          "conversation_id": conversation_id,
          "full_response": complete_response,
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
    
    # Filter out system messages so they don't appear in the frontend UI
    return [msg for msg in messages if msg.role != "system"]

@router.delete("/conversation/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    await delete_conversation(conversation_id)
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
