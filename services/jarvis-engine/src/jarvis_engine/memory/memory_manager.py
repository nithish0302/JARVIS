import json
import re
import uuid
from datetime import datetime
import aiosqlite
from ..core.config import settings

class MemoryManager:

  async def save_memory(
    self,
    content: str,
    category: str = "general",
    importance: int = 5,
    source_conversation_id: str = None
  ) -> str:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        
        # Check for duplicate - same content exists?
        # Use first 100 chars for comparison
        content_prefix = content[:100].lower()
        cursor = await db.execute(
            """SELECT id FROM memories 
               WHERE LOWER(SUBSTR(content, 1, 100)) = ?
               LIMIT 1""",
            (content_prefix,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            # Memory already exists, just update 
            # access time and return existing ID
            await db.execute(
                """UPDATE memories 
                   SET last_accessed = datetime('now'),
                   access_count = access_count + 1
                   WHERE id = ?""",
                (existing[0],)
            )
            await db.commit()
            return existing[0]
        
        # New memory - save it
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        await db.execute(
            """INSERT INTO memories 
               (id, content, category, importance,
                created_at, last_accessed, access_count,
                source_conversation_id)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
            (memory_id, content, category, importance,
             now, now, source_conversation_id)
        )
        await db.commit()
        return memory_id

  async def get_relevant_memories(
    self,
    query: str,
    limit: int = 5
  ) -> list[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Split query into words and search each
        words = [
            w.lower() for w in query.split() 
            if len(w) > 3  # Skip short words
        ]
        
        if not words:
            # If no meaningful words, return top memories
            cursor = await db.execute(
                """SELECT * FROM memories 
                   ORDER BY importance DESC, 
                   last_accessed DESC 
                   LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        
        # Build OR query for all words
        conditions = " OR ".join(
            ["LOWER(content) LIKE ?" for _ in words]
        )
        params = [f"%{w}%" for w in words]
        params.append(limit)
        
        cursor = await db.execute(
            f"""SELECT * FROM memories 
                WHERE {conditions}
                ORDER BY importance DESC, 
                last_accessed DESC 
                LIMIT ?""",
            params
        )
        rows = await cursor.fetchall()
        results = [dict(row) for row in rows]
        
        # Update access stats
        if results:
            ids = [r["id"] for r in results]
            placeholders = ",".join(["?" for _ in ids])
            now = datetime.utcnow().isoformat() + "Z"
            await db.execute(
                f"""UPDATE memories 
                    SET last_accessed = ?,
                    access_count = access_count + 1
                    WHERE id IN ({placeholders})""",
                [now] + ids
            )
            await db.commit()
        
        return results

  async def get_all_memories(
    self,
    limit: int = 50
  ) -> list[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM memories ORDER BY importance DESC, created_at DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

  async def delete_memory(
    self, memory_id: str
  ) -> bool:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        await db.commit()
        return deleted

  async def extract_and_save_memories(
    self,
    user_message: str,
    conversation_id: str = None
  ) -> list[str]:
    saved = []
    msg_clean = user_message.strip()
    
    # Skip very short messages
    if len(msg_clean) < 10:
      return saved
    
    if not settings.GROQ_API_KEY:
      return saved

    try:
      from groq import AsyncGroq
      client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=2.0)
      
      prompt = (
        "You are a memory extraction assistant for JARVIS AI.\n"
        "Analyze the user's message and determine if it contains genuine long-term facts, "
        "preferences, background information, or project details about the user that are "
        "worth remembering for future conversations.\n\n"
        "Guidelines:\n"
        "- DO NOT save questions, transient doubts, momentary commands, greetings, "
        "troubleshooting queries, or general discussions (e.g. 'how do i use X', "
        "'i am not sure if X works', 'what is Y', 'open spotify').\n"
        "- DO save enduring personal facts, user preferences, user bio/identity, "
        "hardware/software setup, active projects, and long-term goals (e.g. "
        "'i am a developer building JARVIS with Tauri', 'my favorite language is Rust', "
        "'i use dual 4K monitors', 'call me Alex').\n\n"
        "Respond with ONLY a JSON object formatted as:\n"
        "{\n"
        '  "should_save": true or false,\n'
        '  "content": "Clean, concise statement of the fact or empty string if not saving",\n'
        '  "category": "personal" | "preference" | "project" | "goal" | "fact",\n'
        '  "importance": integer from 1 to 10\n'
        "}\n"
        'If should_save is false: {"should_save": false, "content": "", "category": "general", "importance": 0}'
      )

      models_to_try = ["groq/compound-mini", "groq/compound"]
      
      data = None
      for model in models_to_try:
        try:
          resp = await client.chat.completions.create(
            model=model,
            messages=[
              {"role": "system", "content": prompt},
              {"role": "user", "content": msg_clean}
            ],
            temperature=0.0,
            max_tokens=150
          )
          raw_text = resp.choices[0].message.content.strip()
          match = re.search(r'\{[\s\S]*\}', raw_text)
          if match:
            data = json.loads(match.group())
            break
        except Exception:
          continue

      if not data or not isinstance(data, dict):
        return saved

      should_save = data.get("should_save", False)
      if not should_save:
        return saved

      content = data.get("content", "").strip() or msg_clean
      category = str(data.get("category", "general")).lower()
      if category not in ["personal", "preference", "project", "goal", "fact"]:
        category = "general"
      
      try:
        importance = max(1, min(10, int(data.get("importance", 5))))
      except (ValueError, TypeError):
        importance = 5

      memory_id = await self.save_memory(
        content=content,
        category=category,
        importance=importance,
        source_conversation_id=conversation_id
      )
      saved.append(content)
      print(f"[MEMORY EXTRACTED] Category: {category} | Importance: {importance} | Content: {content}")
      return saved

    except Exception as e:
      print(f"[MEMORY] Extraction skipped or failed: {e}")
      return saved

memory_manager = MemoryManager()
