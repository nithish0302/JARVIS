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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS plugin_credentials (
                plugin_id TEXT,
                key TEXT,
                encrypted_blob BLOB,
                created_at TEXT,
                updated_at TEXT,
                PRIMARY KEY (plugin_id, key)
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
        print("[DB] Database initialized with performance indexes and settings table")

async def get_setting(key: str, default: str = "") -> str:
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print(f"[DB] Error reading setting {key}: {e}")
    return default

async def set_setting(key: str, value: str) -> None:
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value)
            )
            await db.commit()
    except Exception as e:
        print(f"[DB] Error writing setting {key}: {e}")

