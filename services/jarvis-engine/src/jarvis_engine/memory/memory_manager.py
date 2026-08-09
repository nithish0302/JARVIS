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
    memory_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            """INSERT INTO memories
               (id, content, category, importance, created_at, last_accessed, access_count, source_conversation_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, content, category, importance, now, now, 0, source_conversation_id)
        )
        await db.commit()
    return memory_id

  async def get_relevant_memories(
    self,
    query: str,
    limit: int = 5
  ) -> list[dict]:
    query_words = [w.lower() for w in query.split() if len(w) > 3]
    if not query_words:
        return []
    
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        conditions = " OR ".join(["content LIKE ?" for _ in query_words])
        params = [f"%{w}%" for w in query_words]
        
        sql = f"SELECT * FROM memories WHERE {conditions} ORDER BY importance DESC, last_accessed DESC LIMIT ?"
        params.append(limit)
        
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            
        memories = [dict(r) for r in rows]
        
        if memories:
            memory_ids = [m["id"] for m in memories]
            now = datetime.utcnow().isoformat() + "Z"
            placeholders = ",".join(["?"] * len(memory_ids))
            
            await db.execute(
                f"UPDATE memories SET last_accessed = ?, access_count = access_count + 1 WHERE id IN ({placeholders})",
                [now] + memory_ids
            )
            await db.commit()
            
        return memories

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
    conversation_id: str
  ) -> list[str]:
    triggers = {
        "i prefer": ("preference", 6),
        "i like": ("preference", 6),
        "i am": ("personal", 8),
        "i'm": ("personal", 8),
        "i work on": ("project", 7),
        "i'm building": ("project", 7),
        "remember that": ("general", 5),
        "my name is": ("personal", 8),
        "i have": ("fact", 8),
        "i want to": ("goal", 7),
        "my goal is": ("goal", 7)
    }
    
    saved = []
    msg_lower = user_message.lower()
    
    for trigger, (category, importance) in triggers.items():
        if trigger in msg_lower:
            await self.save_memory(
                content=user_message,
                category=category,
                importance=importance,
                source_conversation_id=conversation_id
            )
            saved.append(user_message)
            break
            
    return saved

memory_manager = MemoryManager()
