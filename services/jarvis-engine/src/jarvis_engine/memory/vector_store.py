"""ChromaDB-backed semantic memory store (Phase 7 M3).

SQLite (memory_manager.py) stays the single source of truth for memory
content/metadata. This module maintains a parallel embedding index purely
for similarity search - every public function here is best-effort: if
chromadb or the embedding model fails for any reason (no network on the
first model download, a locked file, etc.) callers log and continue,
since losing semantic search must never break the underlying save/edit/
delete, which SQLite already handles independently.

Model: all-MiniLM-L6-v2 (~90MB on disk, 384-dim output) - the smallest
widely-used sentence-transformers model, chosen because this machine
already carries Whisper + Kokoro. It is forced onto CPU (encoding a short
memory string takes low milliseconds there) so it never competes with
Whisper/Kokoro for the 4GB card's VRAM, and it is loaded lazily - only on
the first embed/search call that actually needs it - so a restart with
nothing new to embed (the common case once the retrofit migration has
run once) costs nothing extra.
"""
import asyncio
import os
import threading

from ..core.config import settings

_EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
_COLLECTION_NAME = "memories"

_model = None
_model_lock = threading.Lock()
_collection = None
_chroma_lock = threading.Lock()


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    with _chroma_lock:
        if _collection is not None:
            return _collection
        import chromadb
        chroma_path = getattr(settings, "CHROMA_PATH", "data/chroma")
        os.makedirs(chroma_path, exist_ok=True)
        client = chromadb.PersistentClient(path=chroma_path)
        _collection = client.get_or_create_collection(_COLLECTION_NAME)
        return _collection


def _get_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        from sentence_transformers import SentenceTransformer
        print(f"[VECTOR STORE] Loading embedding model {_EMBED_MODEL_NAME} on CPU...")
        _t0 = __import__("time").time()
        _model = SentenceTransformer(_EMBED_MODEL_NAME, device="cpu")
        print(f"[VECTOR STORE] Embedding model ready ({__import__('time').time() - _t0:.2f}s)")
        return _model


def _embed_sync(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return model.encode(list(texts), convert_to_numpy=True).tolist()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(_embed_sync, texts)


def _upsert_sync(memory_id: str, content: str, category: str, importance: int) -> None:
    collection = _get_collection()
    embedding = _embed_sync([content])[0]
    collection.upsert(
        ids=[memory_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"category": category or "general", "importance": int(importance or 5)}],
    )


async def upsert_memory(
    memory_id: str, content: str, category: str = "general", importance: int = 5
) -> None:
    try:
        await asyncio.to_thread(_upsert_sync, memory_id, content, category, importance)
    except Exception as e:
        print(f"[VECTOR STORE] Failed to embed memory {memory_id}: {e}")


def _delete_sync(memory_id: str) -> None:
    collection = _get_collection()
    collection.delete(ids=[memory_id])


async def delete_memory(memory_id: str) -> None:
    try:
        await asyncio.to_thread(_delete_sync, memory_id)
    except Exception as e:
        print(f"[VECTOR STORE] Failed to delete embedding for {memory_id}: {e}")


def _search_sync(query: str, limit: int) -> list[dict]:
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []
    query_embedding = _embed_sync([query])[0]
    result = collection.query(query_embeddings=[query_embedding], n_results=min(limit, count))
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    return [{"id": mid, "distance": dist} for mid, dist in zip(ids, distances)]


async def semantic_search(query: str, limit: int = 10) -> list[dict]:
    """Returns [{id, distance}, ...] ranked nearest-first. distance is
    cosine distance (chroma's default) - lower is more similar."""
    try:
        return await asyncio.to_thread(_search_sync, query, limit)
    except Exception as e:
        print(f"[VECTOR STORE] Semantic search failed: {e}")
        return []


def _migrate_sync(memories: list[dict]) -> int:
    if not memories:
        return 0
    collection = _get_collection()
    all_ids = [m["id"] for m in memories]

    # Cheap existence check BEFORE touching the embedding model - if
    # everything is already embedded (the common case on every restart
    # after the first), this returns without ever loading
    # sentence-transformers, so a fully-migrated DB costs nothing extra.
    existing_ids = set()
    CHUNK = 500
    for i in range(0, len(all_ids), CHUNK):
        chunk_ids = all_ids[i:i + CHUNK]
        got = collection.get(ids=chunk_ids)
        existing_ids.update(got.get("ids", []))

    missing = [m for m in memories if m["id"] not in existing_ids]
    if not missing:
        return 0

    print(f"[VECTOR STORE] Retrofit migration: embedding {len(missing)} existing memories...")
    texts = [m["content"] for m in missing]
    embeddings = _embed_sync(texts)
    collection.upsert(
        ids=[m["id"] for m in missing],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "category": m.get("category") or "general",
                "importance": int(m.get("importance") or 5),
            }
            for m in missing
        ],
    )
    print(f"[VECTOR STORE] Retrofit migration complete: {len(missing)} memories embedded")
    return len(missing)


async def migrate_existing_memories(memories: list[dict]) -> int:
    """One-time backfill for memories that predate the embedding index.
    Safe to call on every startup - idempotent, and cheap (no model load)
    once nothing is missing."""
    try:
        return await asyncio.to_thread(_migrate_sync, memories)
    except Exception as e:
        print(f"[VECTOR STORE] Retrofit migration failed: {e}")
        return 0
