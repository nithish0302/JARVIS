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
        await db.commit()
