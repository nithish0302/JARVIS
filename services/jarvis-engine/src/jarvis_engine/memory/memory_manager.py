import difflib
import json
import re
import uuid
from datetime import datetime

import aiosqlite

from ..core.config import settings
from . import vector_store

NEAR_DUPLICATE_THRESHOLD = 0.85


def normalize_memory_content(content: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace so near-identical
    phrasings ("I'm a developer." vs "im a developer") normalize the same."""
    text = content.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def content_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(
        None, normalize_memory_content(a), normalize_memory_content(b)
    ).ratio()


class MemoryManager:
    async def save_memory(
        self,
        content: str,
        category: str = "general",
        importance: int = 5,
        source_conversation_id: str | None = None,
    ) -> str:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            # Check for duplicate - same content exists?
            # Use first 100 chars for comparison
            content_prefix = content[:100].lower()
            cursor = await db.execute(
                """SELECT id FROM memories
               WHERE LOWER(SUBSTR(content, 1, 100)) = ?
               LIMIT 1""",
                (content_prefix,),
            )
            existing = await cursor.fetchone()

            if not existing:
                # Fuzzy pass: same fact, different phrasing. Scoped to the same
                # category so this stays cheap and doesn't cross-match e.g. a
                # "preference" memory against an unrelated "project" one.
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, content, importance FROM memories WHERE category = ?",
                    (category,),
                )
                candidates = await cursor.fetchall()
                db.row_factory = None
                for candidate in candidates:
                    if (
                        content_similarity(content, candidate["content"])
                        >= NEAR_DUPLICATE_THRESHOLD
                    ):
                        existing = (candidate["id"],)
                        if importance > candidate["importance"]:
                            await db.execute(
                                "UPDATE memories SET importance = ? WHERE id = ?",
                                (importance, candidate["id"]),
                            )
                        break

            if existing:
                # Memory already exists (exact or near-duplicate), just update
                # access time and return existing ID
                await db.execute(
                    """UPDATE memories
                   SET last_accessed = datetime('now'),
                   access_count = access_count + 1
                   WHERE id = ?""",
                    (existing[0],),
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
                (
                    memory_id,
                    content,
                    category,
                    importance,
                    now,
                    now,
                    source_conversation_id,
                ),
            )
            await db.commit()

        # Best-effort - vector_store swallows its own errors, so a slow model
        # load or a chroma hiccup never blocks the memory actually being saved.
        await vector_store.upsert_memory(memory_id, content, category, importance)
        return memory_id

    async def get_relevant_memories(self, query: str, limit: int = 5) -> list[dict]:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Split query into words and search each
            words = [
                w.lower()
                for w in query.split()
                if len(w) > 3  # Skip short words
            ]

            if not words:
                # If no meaningful words, return top memories
                cursor = await db.execute(
                    """SELECT * FROM memories 
                   ORDER BY importance DESC, 
                   last_accessed DESC 
                   LIMIT ?""",
                    (limit,),
                )
                rows = await cursor.fetchall()
                return self._dedupe_near_identical([dict(row) for row in rows])

            # Build OR query for all words
            conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in words])
            params: list[str | int] = [f"%{w}%" for w in words]
            params.append(limit)

            cursor = await db.execute(
                f"""SELECT * FROM memories 
                WHERE {conditions}
                ORDER BY importance DESC, 
                last_accessed DESC 
                LIMIT ?""",
                params,
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
                    [now] + ids,
                )
                await db.commit()

            # Semantic fallback: only kicks in when the keyword pass didn't
            # already fill the requested limit, so a query that keyword-matches
            # plenty of memories (e.g. the existing "quasarnetics" ranking
            # behavior) is completely unaffected - this only ever ADDS results
            # a pure LIKE-based search would have missed (conceptually related,
            # no shared keywords), never re-ranks or replaces what's already
            # there.
            missing = limit - len(results)
            if missing > 0:
                existing_ids = {r["id"] for r in results}
                semantic_hits = await vector_store.semantic_search(
                    query, limit=missing + len(existing_ids)
                )
                fill_ids = [
                    h["id"] for h in semantic_hits if h["id"] not in existing_ids
                ][:missing]
                if fill_ids:
                    placeholders = ",".join(["?" for _ in fill_ids])
                    cursor = await db.execute(
                        f"SELECT * FROM memories WHERE id IN ({placeholders})", fill_ids
                    )
                    extra_rows = await cursor.fetchall()
                    # Preserve semantic-similarity order rather than SQL's
                    # arbitrary IN(...) row order.
                    by_id = {row["id"]: dict(row) for row in extra_rows}
                    extra = [by_id[i] for i in fill_ids if i in by_id]

                    if extra:
                        now = datetime.utcnow().isoformat() + "Z"
                        extra_placeholders = ",".join(["?" for _ in extra])
                        await db.execute(
                            f"""UPDATE memories
                            SET last_accessed = ?,
                            access_count = access_count + 1
                            WHERE id IN ({extra_placeholders})""",
                            [now] + [e["id"] for e in extra],
                        )
                        await db.commit()
                        results = results + extra

            return self._dedupe_near_identical(results)

    @staticmethod
    def _dedupe_near_identical(results: list[dict]) -> list[dict]:
        """Drop near-identical memories from the same injection batch before
        they reach the prompt. Similarity is transitive - two paraphrases can
        each be >=85% similar to a third memory without being similar enough to
        each other directly (e.g. "with Tauri" vs "using Tauri" wording drift
        across a chain of near-dupes) - so this unions every pair above the
        threshold into clusters (not just "compare against what's already kept")
        and keeps one representative per cluster. `results` already arrives
        ordered importance-first / most-recent-first (keyword matches) followed
        by semantic-fallback extras, so keeping the first (lowest-index) member
        of each cluster keeps the most important/recent copy."""
        n = len(results)
        parent = list(range(n))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int) -> None:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[max(ri, rj)] = min(ri, rj)

        for i in range(n):
            for j in range(i + 1, n):
                if (
                    content_similarity(results[i]["content"], results[j]["content"])
                    >= NEAR_DUPLICATE_THRESHOLD
                ):
                    union(i, j)

        seen_clusters: set[int] = set()
        deduped: list[dict] = []
        for i in range(n):
            root = find(i)
            if root in seen_clusters:
                continue
            seen_clusters.add(root)
            deduped.append(results[i])
        return deduped

    async def migrate_embeddings(self) -> int:
        """Retrofit: embed any existing memory that predates the embedding
        index. Safe to call on every startup - vector_store checks what's
        already embedded before loading the model, so this is a no-op cost
        once the backfill has run once."""
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, content, category, importance FROM memories"
            )
            rows = await cursor.fetchall()
        return await vector_store.migrate_existing_memories([dict(r) for r in rows])

    async def get_all_memories(self, limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM memories ORDER BY importance DESC, created_at DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        category: str | None = None,
        importance: int | None = None,
    ) -> dict | None:
        """Partial update - only fields that are not None are changed. Returns
        the updated record, or None if no memory with that id exists."""
        fields = []
        params = []
        if content is not None:
            fields.append("content = ?")
            params.append(content)
        if category is not None:
            fields.append("category = ?")
            params.append(category)
        if importance is not None:
            fields.append("importance = ?")
            params.append(importance)

        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            if fields:
                params.append(memory_id)
                await db.execute(
                    f"UPDATE memories SET {', '.join(fields)} WHERE id = ?", params
                )
                await db.commit()

            cursor = await db.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            )
            row = await cursor.fetchone()
            updated = dict(row) if row else None

        # Re-embed only on a genuine content change - category/importance-only
        # edits don't invalidate the existing embedding.
        if updated and content is not None:
            await vector_store.upsert_memory(
                memory_id,
                updated["content"],
                updated["category"],
                updated["importance"],
            )
        return updated

    async def delete_memory(self, memory_id: str) -> bool:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            cursor = await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            deleted = cursor.rowcount > 0
            await db.commit()
        if deleted:
            await vector_store.delete_memory(memory_id)
        return deleted

    async def extract_and_save_memories(
        self, user_message: str, conversation_id: str | None = None
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
                            {"role": "user", "content": msg_clean},
                        ],
                        temperature=0.0,
                        max_tokens=150,
                    )
                    raw_text = (resp.choices[0].message.content or "").strip()
                    match = re.search(r"\{[\s\S]*\}", raw_text)
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
                source_conversation_id=conversation_id,
            )
            saved.append(content)
            if settings.DEBUG_LOG_CONTENT:
                print(
                    f"[MEMORY EXTRACTED] Category: {category} | Importance: {importance} | Content: {content}"
                )
            return saved

        except Exception as e:
            print(f"[MEMORY] Extraction skipped or failed: {e}")
            return saved


memory_manager = MemoryManager()
