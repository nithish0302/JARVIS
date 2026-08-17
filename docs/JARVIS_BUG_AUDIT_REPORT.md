# JARVIS ENGINE - BUG AUDIT REPORT

**Generated:** August 17, 2026  
**Audited Files:**
- services/jarvis-engine/src/jarvis_engine/api/routes.py
- services/jarvis-engine/src/jarvis_engine/tools/web_search.py
- services/jarvis-engine/src/jarvis_engine/tools/search_detector.py
- services/jarvis-engine/src/jarvis_engine/providers/ (all)
- services/jarvis-engine/src/jarvis_engine/memory/ (all)
- services/jarvis-engine/src/jarvis_engine/core/ (all)

---

## EXECUTIVE SUMMARY

This report documents a comprehensive security and code quality audit of the JARVIS Engine codebase. The audit focused on:

- API routes and endpoint security
- Web search integration and tools
- Provider implementations (Ollama, OpenRouter, Groq, Gemini)
- Memory management and persistence
- Core configuration and database layer

### Summary Statistics

| Priority | Count | Category |
|----------|-------|----------|
| **P1 Critical** | 5 | Race conditions, blocking I/O, SQL injection, path traversal |
| **P2 High** | 7 | Error handling, inconsistent logic, fallback issues |
| **P3 Medium** | 17 | Search detection, rate limiting, timestamp issues, orphaned data |
| **P4 Low** | 6 | Code quality, type hints, magic numbers, logging |
| **TOTAL** | **35** | All categories |

---

## P1 - CRITICAL BUGS

### 1. Race Condition: Parallel Web Search + AI Response

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:194-198`

**Code:**
```python
search_results, ai_response = await asyncio.gather(
    search_web(search_query_used, max_results=4),
    provider_manager.chat(full_messages),
    return_exceptions=True
)
```

**Issue:** AI response is generated **in parallel** with web search, meaning the AI receives NO search results when generating its response. The search results arrive too late to be used.

**Impact:** AI answers questions without the search context it needs, defeating the purpose of web search.

---

### 2. Exception Handling Silently Swallows Errors

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:215-220`

**Code:**
```python
if isinstance(ai_response, Exception):
    response_text = "I encountered an error."
    provider_used = "error"
    model_used = "error"
```

**Issue:** No logging or error details. Users get generic "I encountered an error" with no diagnostics.

**Impact:** Impossible to debug AI provider failures.

---

### 3. Synchronous Groq Client in Async Context

**File:** `services/jarvis-engine/src/jarvis_engine/providers/groq_provider.py:28-44, 54-69`

**Code:**
```python
client = Groq(api_key=settings.GROQ_API_KEY)  # Synchronous client
response = client.chat.completions.create(...)  # Blocking call
```

**Issue:** Blocking I/O in async functions blocks the entire event loop.

**Impact:** Application freezes during Groq API calls, affecting all concurrent requests.

---

### 4. SQL Injection Vulnerability

**File:** `services/jarvis-engine/src/jarvis_engine/memory/memory_manager.py:90-94`

**Code:**
```python
conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in words])
cursor = await db.execute(
    f"""SELECT * FROM memories 
        WHERE {conditions}  # String interpolation!
        ORDER BY importance DESC, 
        last_accessed DESC 
        LIMIT ?""",
    params
)
```

**Issue:** While params are parameterized, the dynamic SQL construction is fragile and prone to errors.

**Impact:** Potential SQL injection if code is modified incorrectly in the future.

---

### 5. Path Traversal Vulnerability

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:583-584, 595-596, 607-608`

**Code:**
```python
env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    ".env"
)
```

**Issue:** No validation that the computed path is within the expected directory. Vulnerable to symlink attacks.

**Impact:** API keys could be written to arbitrary files.

---

## P2 - HIGH PRIORITY BUGS

### 6. Memory Deduplication is Case-Sensitive on Content

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:558-565`

**Code:**
```python
await db.execute("""
  DELETE FROM memories 
  WHERE id NOT IN (
    SELECT MIN(id) 
    FROM memories 
    GROUP BY LOWER(SUBSTR(content, 1, 100))
  )
""")
```

**Issue:** The deduplication groups by lowercase prefix, but `save_memory` checks exact case match at line 22. Inconsistent behavior.

**Impact:** Duplicates may not be properly detected.

---

### 7. Missing Error Handling on set_key()

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:584, 596, 608`

**Code:**
```python
set_key(env_path, "OPENROUTER_API_KEY", key)  # No try/except
```

**Issue:** If `.env` file is missing or write fails, endpoint crashes with 500.

**Impact:** Poor UX when .env file doesn't exist.

---

### 8. asyncio.wait_for() Returns Cancelled Task on Timeout

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:381-383`

**Code:**
```python
search_results = await asyncio.wait_for(search_task, timeout=10.0)
if search_results:  # May be None or empty list
```

**Issue:** `asyncio.TimeoutError` is caught but the task may return `None` on cancellation, not handled properly.

**Impact:** Search results may be silently lost.

---

### 9. Provider Fallback Logic Broken in Stream Endpoint

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:352-375`

**Code:**
```python
try:
    async for token in provider.stream(full_messages):
        full_response_parts.append(token)
        yield json_module.dumps({"type": "token", "content": token}) + "\n"
    break
except Exception as stream_err:
    if full_response_parts:
        break  # Can't fallback if already yielded
    continue
```

**Issue:** If first provider starts yielding tokens then crashes mid-stream, user gets partial response with no error indication.

**Impact:** Silent failures, incomplete responses.

---

### 10. Redundant Provider Name Logic

**File:** `services/jarvis-engine/src/jarvis_engine/providers/groq_provider.py:30-33`

**Code:**
```python
groq_messages = [
    {
        "role": m.role if m.role != "assistant" else "assistant",
        "content": m.content
    }
]
```

**Issue:** Condition `if m.role != "assistant" else "assistant"` is always "assistant" when true, makes no sense.

**Impact:** Logic error, likely meant to filter or transform roles differently.

---

### 11. Inconsistent Message Filtering Across Providers

**Files:**
- `openrouter.py:46-47` filters empty system messages
- `groq_provider.py:37` filters only specific roles
- `gemini_provider.py:30-31` filters all system messages
- `ollama.py` does NO filtering

**Issue:** Different providers handle message lists differently, leading to inconsistent behavior.

**Impact:** Same input produces different results across providers.

---

### 12. Missing await on Provider Deletion in Conversation

**File:** `services/jarvis-engine/src/jarvis_engine/memory/conversation.py:130-132`

**Code:**
```python
cursor = await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
deleted = cursor.rowcount > 0  # cursor.rowcount is async
```

**Issue:** `cursor.rowcount` might not be immediately available; should be awaited or checked differently.

**Impact:** Incorrect deletion confirmation.

---

## P3 - MEDIUM PRIORITY BUGS

### 13. Naive String Matching for Search Detection

**File:** `services/jarvis-engine/src/jarvis_engine/tools/search_detector.py:19-46`

**Issue:** Uses simple substring matching like `"what is the current"` to detect search needs. Easily fooled by:
- "what is the current implementation of X" (code question, not search)
- "show my current settings" (UI command)

**Impact:** False positives trigger unnecessary web searches.

---

### 14. No Rate Limiting on API Endpoints

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py` (all endpoints)

**Issue:** No rate limiting, authentication, or throttling on any endpoint.

**Impact:** Vulnerable to abuse, DoS attacks, API key exhaustion.

---

### 15. Memory Access Count Update is Inconsistent

**File:** `services/jarvis-engine/src/jarvis_engine/memory/memory_manager.py:100-112`

**Issue:** Access count is updated in `get_relevant_memories()` but NOT in `get_all_memories()`. Inconsistent tracking.

**Impact:** Access statistics are unreliable.

---

### 16. Conversation Title Uniqueness Check is Case-Insensitive

**File:** `services/jarvis-engine/src/jarvis_engine/memory/conversation.py:60-63`

**Code:**
```python
cursor = await db.execute(
    "SELECT id FROM conversations WHERE LOWER(title) = LOWER(?) AND id != ?",
    (new_title, conversation_id)
)
```

**Issue:** Prevents "Project A" and "project a" from coexisting, but allows "Project A" and "Project  A" (extra space).

**Impact:** Confusing UX, title conflicts.

---

### 17. SEARCH_STRICT_INSTRUCTION Applied Globally

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:156`

**Code:**
```python
search_context_accumulated += "\n" + SEARCH_STRICT_INSTRUCTION
```

**Issue:** Instruction to "use ONLY search results" is added to ALL messages in a conversation where search was performed once, even if later messages don't need search.

**Impact:** AI becomes overly conservative, refusing to answer from knowledge even when appropriate.

---

### 18. Hardcoded Snippet Length Truncation

**File:** `services/jarvis-engine/src/jarvis_engine/tools/web_search.py:32, 58`

**Code:**
```python
"snippet": r.get("content", "")[:300],  # Tavily
"snippet": r.get("body", "")[:300],      # DuckDuckGo
```

**Issue:** Hardcoded 300 char limit may cut off mid-sentence. No ellipsis added.

**Impact:** Confusing, incomplete snippets.

---

### 19. DuckDuckGo Synchronous Context Manager in Async Function

**File:** `services/jarvis-engine/src/jarvis_engine/tools/web_search.py:46-50`

**Code:**
```python
with DDGS() as ddgs:  # Synchronous
    for r in ddgs.text(query, max_results=max_results):  # Blocking
```

**Issue:** Blocking I/O in async function. Blocks event loop.

**Impact:** Application freezes during DuckDuckGo searches.

---

### 20. Empty SearchResult Class

**File:** `services/jarvis-engine/src/jarvis_engine/tools/web_search.py:5-9`

**Code:**
```python
class SearchResult:
  title: str
  url: str
  snippet: str
  source: str
```

**Issue:** Not a dataclass or Pydantic model. Just a class with type hints that do nothing.

**Impact:** Doesn't enforce types, serves no purpose.

---

### 21. Timestamp Format Inconsistency

**Files:**
- `memory_manager.py:43` uses `datetime.utcnow().isoformat() + "Z"`
- `conversation.py:10` uses `datetime.datetime.now().isoformat()` (no Z, no UTC)

**Issue:** Mixed timezone handling. Some timestamps are UTC, some are local.

**Impact:** Time-based queries and sorting may be incorrect.

---

### 22. No Cleanup of Orphaned Messages

**File:** `services/jarvis-engine/src/jarvis_engine/memory/conversation.py:50-54`

**Issue:** `delete_conversation()` deletes conversation and messages, but memories table has `source_conversation_id` that becomes orphaned.

**Impact:** Database accumulates orphaned memory references.

---

### 23. Gemini API Key Exposed in URL

**File:** `services/jarvis-engine/src/jarvis_engine/providers/gemini_provider.py:58, 85`

**Code:**
```python
url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
```

**Issue:** API key exposed in URL query parameter (logged by proxies/load balancers).

**Impact:** API key leak in logs.

---

### 24. Missing Validation on Memory Importance

**File:** `services/jarvis-engine/src/jarvis_engine/core/models.py:38`

**Code:**
```python
importance: int = 5
```

**Issue:** No validation that importance is within a valid range (e.g., 1-10).

**Impact:** Can insert negative or extremely large importance values.

---

### 25. Magic Numbers Everywhere

**Examples:**
- `routes.py:194` - max_results=4
- `routes.py:206` - search_sources[:3]
- `memory_manager.py:222` - memory_content[:200]
- `search_detector.py:28` - len(msg_lower) < 8

**Issue:** No constants defined, hard to maintain.

**Impact:** Difficult to tune behavior.

---

### 26. Inconsistent Exception Handling

**Files:** All provider files

**Issue:**
- `ollama.py` returns error strings
- `openrouter.py` returns error strings
- `groq_provider.py` returns error strings but raises in stream
- `gemini_provider.py` raises in stream

**Impact:** Mixing `return "error"` with `raise e` makes error handling unpredictable.

---

### 27. No Input Validation on Query Length

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:26-30`

**Code:**
```python
query = request.get("query", "")
if not query:
    raise HTTPException(status_code=400, detail="Query is required")
```

**Issue:** No max length check. Can send gigabyte-sized query.

**Impact:** Potential DoS via large payloads.

---

### 28. Provider Availability Checked Twice

**File:** `services/jarvis-engine/src/jarvis_engine/providers/manager.py:28-35`

**Issue:** `chat()` calls `is_available()` before `chat()`, but provider's `chat()` method also handles unavailability.

**Impact:** Redundant checks, slower performance.

---

### 29. Empty Catch-All Exception Handlers

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:336-344, 376-377, 452-453`

**Code:**
```python
except Exception as meta_err:
    print(f"Meta chunk error: {meta_err}")  # Only prints
```

**Issue:** Prints to stdout instead of proper logging. No structured error tracking.

**Impact:** Errors are lost in production.

---

## P4 - LOW PRIORITY / CODE QUALITY

### 30. Gemini _format_messages Returns Tuple Without Correct Type Hint

**File:** `services/jarvis-engine/src/jarvis_engine/providers/gemini_provider.py:24-37`

**Code:**
```python
def _format_messages(self, messages: list[Message]) -> list[dict]:
    # ...
    return formatted, system_msg  # Returns tuple!
```

**Issue:** Return type annotation is incorrect.

**Impact:** Type checkers will fail.

---

### 31. Settings Mutation at Runtime

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:586, 598, 610`

**Code:**
```python
settings.OPENROUTER_API_KEY = key  # Mutates global settings
```

**Issue:** `Settings` object is meant to be immutable. Mutating it doesn't affect other imports.

**Impact:** Changes don't propagate to already-imported providers.

---

### 32. No Database Migration Strategy

**File:** `services/jarvis-engine/src/jarvis_engine/core/database.py:5-43`

**Issue:** Uses `CREATE TABLE IF NOT EXISTS` with no versioning or migration system.

**Impact:** Cannot safely evolve schema.

---

### 33. UI Action Tags Embedded in Response Text

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:96-99`

**Code:**
```python
# Never show the raw tag text to the user
```

**Issue:** Comment says "never show raw tag" but tags are in the assistant's text response, visible if frontend doesn't strip them.

**Impact:** User sees `[UI_ACTION:chat_mode_on]` in messages if frontend breaks.

---

### 34. Conversation ID Optional But Always Required

**File:** `services/jarvis-engine/src/jarvis_engine/core/models.py:11`

**Code:**
```python
conversation_id: str | None = None
```

**Issue:** Every endpoint immediately assigns a UUID if None, so it's never actually None after the first line.

**Impact:** Misleading type hint.

---

### 35. Unused Import Inside Function

**File:** `services/jarvis-engine/src/jarvis_engine/api/routes.py:524`

**Code:**
```python
from datetime import datetime  # Only used in this endpoint
```

**Issue:** Imported inside function instead of at module level.

**Impact:** Inconsistent style.

---

## RECOMMENDATIONS

### Immediate Actions (P1 Issues)

1. **Fix race condition in web search:** Await search results before passing to AI
2. **Replace synchronous Groq client** with async httpx calls
3. **Add proper error logging** with structured logging framework
4. **Validate and sanitize file paths** in API key configuration endpoints
5. **Review SQL query construction** for injection vulnerabilities

### Short-term Actions (P2 Issues)

1. **Standardize message filtering** across all providers
2. **Implement consistent error handling** strategy
3. **Add comprehensive try/except blocks** with proper error propagation
4. **Fix stream fallback logic** to handle partial failures
5. **Add validation** for all user inputs

### Long-term Improvements (P3/P4 Issues)

1. **Implement rate limiting** and authentication on all endpoints
2. **Replace blocking I/O** with async equivalents throughout
3. **Define configuration constants** for all magic numbers
4. **Implement database migration system** (Alembic)
5. **Add comprehensive input validation** with Pydantic
6. **Implement structured logging** (structlog or loguru)
7. **Add type checking** to CI/CD pipeline (mypy)
8. **Create API documentation** (OpenAPI/Swagger)

---

**End of Report**

*JARVIS Engine Bug Audit - August 17, 2026 - Confidential*
