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
    conversation_id: str
  ) -> list[str]:
    saved = []
    msg_lower = user_message.lower().strip()
    
    # Skip very short messages
    if len(msg_lower) < 10:
        return saved
    
    # Expanded triggers - more natural language
    preference_triggers = [
        "i prefer", "i like", "i love", "i enjoy",
        "i hate", "i don't like", "i dislike",
        "i always", "i usually", "i never",
        "my favorite", "i find it", "i think",
    ]
    
    personal_triggers = [
        "my name is", "i am ", "i'm ", "i work",
        "i live", "i study", "i'm from",
        "call me", "you can call me",
    ]
    
    project_triggers = [
        "i'm building", "i'm working on", 
        "i'm developing", "my project",
        "we're building", "i'm creating",
        "i'm making", "my app", "my system",
    ]
    
    goal_triggers = [
        "i want to", "i need to", "my goal",
        "i'm trying to", "i plan to",
        "i hope to", "i wish",
    ]
    
    fact_triggers = [
        "i have", "my pc", "my computer",
        "my laptop", "my setup", "i use",
        "i'm using", "i run", "i installed",
    ]
    
    # Check each category
    category = None
    importance = 5
    
    for trigger in preference_triggers:
        if trigger in msg_lower:
            category = "preference"
            importance = 6
            break
    
    if not category:
        for trigger in personal_triggers:
            if trigger in msg_lower:
                category = "personal"
                importance = 8
                break
    
    if not category:
        for trigger in project_triggers:
            if trigger in msg_lower:
                category = "project"
                importance = 7
                break
    
    if not category:
        for trigger in goal_triggers:
            if trigger in msg_lower:
                category = "goal"
                importance = 6
                break
    
    if not category:
        for trigger in fact_triggers:
            if trigger in msg_lower:
                category = "fact"
                importance = 5
                break
    
    # Save if we found a category
    if category:
        # Clean up the memory content
        # Use first 200 chars of message as memory
        memory_content = user_message[:200].strip()
        if len(user_message) > 200:
            memory_content += "..."
        
        # Prefix with context
        memory_content = f"Nithish said: {memory_content}"
        
        memory_id = await self.save_memory(
            content=memory_content,
            category=category,
            importance=importance,
            source_conversation_id=conversation_id
        )
        saved.append(memory_content)
    
    return saved

memory_manager = MemoryManager()
