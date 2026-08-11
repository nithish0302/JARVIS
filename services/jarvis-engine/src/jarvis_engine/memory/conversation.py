import uuid
import datetime
import aiosqlite
from typing import List
from ..core.models import Message
from ..core.config import settings

async def save_message(conversation_id: str, role: str, content: str, provider_used: str = "", model_used: str = "") -> str:
    msg_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    async with aiosqlite.connect(settings.DB_PATH) as db:
        # Check if conversation exists, if not, create it
        async with db.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (conversation_id, "New Conversation", timestamp, timestamp)
                )
        
        # Save message
        await db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, timestamp, provider_used, model_used) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, timestamp, provider_used, model_used)
        )
        
        # Update conversation updated_at
        await db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (timestamp, conversation_id)
        )
        await db.commit()
        
    return msg_id

async def get_conversation_messages(conversation_id: str) -> List[Message]:
    messages = []
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,)) as cursor:
            async for row in cursor:
                messages.append(Message(
                    role=row["role"],
                    content=row["content"],
                    timestamp=row["timestamp"]
                ))
    return messages

async def delete_conversation(conversation_id: str) -> None:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        await db.commit()

async def get_conversations(limit: int = 10) -> List[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT 
                c.id, c.title, c.created_at, c.updated_at,
                COUNT(m.id) as message_count,
                MIN(CASE WHEN m.role='user' THEN m.content END) as first_message
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            title = row["title"]
            if not title or title == "New Conversation":
                first_msg = row["first_message"] or ""
                title = first_msg[:50]
                if len(first_msg) > 50:
                    title += "..."
                if not title:
                    title = "Untitled conversation"
            result.append({
                "id": row["id"],
                "title": title,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": row["message_count"]
            })
        return result
