import os
import aiosqlite
from .config import settings

async def init_db() -> None:
    # Ensure data directory exists
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                source_conversation_id TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                provider_used TEXT,
                model_used TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        # Performance indexes - added for faster queries
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
            ON messages(conversation_id, timestamp)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_created
            ON memories(created_at DESC)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_conversation
            ON memories(source_conversation_id)
        """)

        await db.commit()
        print("[DB] Database initialized with performance indexes")
