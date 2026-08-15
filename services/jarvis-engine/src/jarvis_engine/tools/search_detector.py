SEARCH_TRIGGERS = [
  "search for", "look up", "find information",
  "what is the latest", "current price",
  "today", "right now", "recent", "news about",
  "who is", "when did", "what happened",
  "how much does", "where is", "what time",
  "weather in", "stock price", "score of",
  "search the web", "search online",
  "google", "find out", "tell me about",
]

UI_EXCLUSIONS = [
  "show my", "open ", "close ", "collapse",
  "expand", "switch to", "go to", "chat mode",
  "graph mode", "show conversations",
  "show skills", "show tools", "show files",
]

def needs_web_search(message: str) -> bool:
  msg_lower = message.lower().strip()

  # Never search for UI commands
  for exc in UI_EXCLUSIONS:
    if exc in msg_lower:
      return False

  # Never search for very short messages
  if len(msg_lower) < 8:
    return False
  
  # Explicit search request
  for trigger in SEARCH_TRIGGERS:
    if trigger in msg_lower:
      return True
  
  # Question words about current events
  question_starters = [
    "what is the current",
    "what are the latest",
    "who won", "who is the",
    "when is the next",
  ]
  for starter in question_starters:
    if msg_lower.startswith(starter):
      return True
  
  return False

def extract_search_query(message: str) -> str:
  msg_lower = message.lower()
  
  # Remove common prefixes to get clean query
  prefixes_to_remove = [
    "search for ", "look up ", "search the web for ",
    "search online for ", "google ", "find ",
    "what is the latest ", "tell me about ",
  ]
  
  for prefix in prefixes_to_remove:
    if msg_lower.startswith(prefix):
      return message[len(prefix):]
  
  return message
