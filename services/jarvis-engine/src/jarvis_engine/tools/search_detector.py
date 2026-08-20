import re

# UI commands - NEVER search these
UI_COMMAND_PATTERNS = [
  r'\bshow\s+(?:my\s+)?(?:skills|tools|files|notes|models|worlds|conversations)\b',
  r'\bopen\s+(?:skills|tools|files|notes|models|worlds|conversations)\b',
  r'\b(?:collapse|expand)\s+(?:the\s+)?graph\b',
  r'\bswitch\s+to\s+(?:chat|graph)\s+mode\b',
  r'\b(?:chat|graph)\s+mode\b',
  r'\bnew\s+chat\b',
  r'\bclear\s+(?:chat|conversation)\b',
  r'\bopen\s+(?:the\s+)?(?:conversation|memory)\s+panel\b',
]

# Explicit search requests
EXPLICIT_SEARCH = re.compile(
  r'(?:search\s+(?:for|about|the|on|online\s+for|the\s+web\s+for)|'
  r'google\s+(?:for\s+)?|look\s+up\s+|find\s+(?:out\s+)?(?:about|the\s+)?|'
  r'(?:me\s+)?information\s+(?:about|on))\s+(.+)',
  re.IGNORECASE
)

# Real-time data patterns
REALTIME_PATTERNS = [
  r'\b(?:latest|breaking|recent|current|today\'?s?)\s+news\b',
  r'\bprice\s+of\s+\w+',
  r'\b\w+\s+price\s*(?:\?|$|\s)',
  r'\bweather\s+in\s+\w+',
  r'\bscore\s+of\b',
  r'\bdid\s+(?:the\s+)?\w+\s+win\b',
  r'\bwho\s+(?:is|was)\s+(?:the\s+)?(?:ceo|cto|president|prime\s+minister|founder|director)\b',
  r'\bwho\s+(?:is|was)\s+[\w\s]+',
  r'\bwhat\s+(?:is|are)\s+the\s+(?:latest|current|new|best)\b',
  r'\bwhat\s+happened\s+(?:to|with|in)\b',
  r'\bis\s+it\s+raining\b',
  r'\b(?:stock|share|crypto|bitcoin|ethereum)\s+(?:price|value|rate)\b',
  r'\b(?:release|launch)\s+date\b',
  r'\bvs\.?\s+.+\s+(?:specs|price|review|comparison)\b',
  r'\bwho\s+won\b',
  r'\bwhen\s+(?:is|was|will)\s+the\b',
  r'\bany\s+(?:new|recent|latest|updated?)\s+(?:news|info|updates?|announcement)\b',
  r'\bwhat\'?s?\s+(?:new|happening|going\s+on)\s+with\b',
  r'\b(?:nvidia|amd|intel|apple|google|meta|microsoft|openai|anthropic|samsung|sony|tesla)\s+(?:news|update|announcement|release|launch)\b',
  r'\b(?:new|latest|recent)\s+(?:from|by|at)\s+\w+\b',
  r'\bany\s+updates?\s+(?:from|on|about)\b',
  r'\bwhat\s+did\s+\w+\s+(?:announce|release|launch|reveal|drop)\b',
  r'\b(?:is|are)\s+there\s+any\s+(?:news|updates?|announcements?)\b',
  r'\bwhat\s+(?:is|are)\s+\w+\s+(?:doing|working\s+on|planning|releasing)\b',
]

# Conversational exclusions - never search
CONVERSATIONAL_EXCLUSIONS = [
  r'\byourself\b',
  r'\byour\s+(?:name|capabilities|features|functions|purpose)\b',
  r'\bhow\s+are\s+you\b',
  r'\bthank\s+you\b',
  r'\bmy\s+code\b',
  r'\bmy\s+function\b',
  r'\bmy\s+project\b',
  r'\bour\s+conversation\b',
  r'\bwe\s+(?:wrote|built|made|created|discussed|talked)\b',
  r'\byou\s+(?:said|told|mentioned|explained)\b',
  r'\bwhat\s+(?:is|are)\s+you\s+(?:doing|working\s+on|planning)\b',
  r'\bwhat\s+did\s+(?:we|you|i)\s+(?:discuss|talk|say|do)\b',
]

def is_ui_command(message: str) -> bool:
  for pattern in UI_COMMAND_PATTERNS:
    if re.search(pattern, message, re.IGNORECASE):
      return True
  return False

def is_conversational(message: str) -> bool:
  for pattern in CONVERSATIONAL_EXCLUSIONS:
    if re.search(pattern, message, re.IGNORECASE):
      return True
  return False

def needs_web_search(message: str) -> bool:
  if len(message.strip()) < 5:
    return False
  if is_ui_command(message):
    return False
  if is_conversational(message):
    return False
  if EXPLICIT_SEARCH.search(message):
    return True
  for pattern in REALTIME_PATTERNS:
    if re.search(pattern, message, re.IGNORECASE):
      return True
  return False

def extract_search_query(message: str) -> str:
  match = EXPLICIT_SEARCH.search(message)
  if match:
    return match.group(1).strip().rstrip('?.,!')
  cleaned = re.sub(
    r'^(?:can you |please |hey |jarvis[,\s]+|'
    r'could you |do you know |tell me )',
    '', message, flags=re.IGNORECASE
  ).strip()
  return cleaned.rstrip('?.,!')
