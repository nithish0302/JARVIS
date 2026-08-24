"""Phase 7 M3: ChromaDB-backed semantic memory search.

These tests exercise real embeddings (no mocking of sentence-transformers
or chromadb) since the entire point being verified is that a conceptually
related query with NO shared keywords still finds the right memory - a
mock would hide exactly the behavior under test.
"""
import uuid
import pytest

from jarvis_engine.memory.memory_manager import memory_manager
from jarvis_engine.memory import vector_store


def _unique_content(label: str) -> str:
    return f"[test-{uuid.uuid4().hex[:8]}] {label}"


@pytest.mark.asyncio
async def test_new_memory_gets_embedded_automatically():
    content = _unique_content("The office espresso machine is broken again")
    memory_id = await memory_manager.save_memory(content=content, category="fact", importance=5)
    try:
        hits = await vector_store.semantic_search(content, limit=5)
        assert any(h["id"] == memory_id for h in hits), (
            "Newly saved memory was not found in the embedding index"
        )
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_semantic_search_finds_conceptually_related_no_shared_keywords():
    """The actual point of semantic vs keyword search: a query that shares
    no keywords with the stored memory must still surface it via meaning."""
    content = _unique_content("Nithish's pet golden retriever is named Max")
    memory_id = await memory_manager.save_memory(content=content, category="personal", importance=6)
    try:
        # "dog" / "puppy" never appear in the stored content at all.
        results = await memory_manager.get_relevant_memories("what kind of dog does he own", limit=5)
        assert any(r["id"] == memory_id for r in results), (
            "Semantic fallback did not surface a conceptually related memory "
            "with zero shared keywords"
        )
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_keyword_rich_query_unaffected_by_semantic_fallback():
    """Regression guard: when the keyword pass already fills `limit`,
    semantic augmentation must not run at all (preserves the existing
    importance-ranking test's exact behavior)."""
    ids = []
    try:
        ids.append(await memory_manager.save_memory(
            content=_unique_content("zylophonics low"), importance=2
        ))
        ids.append(await memory_manager.save_memory(
            content=_unique_content("zylophonics high"), importance=9
        ))
        top_1 = await memory_manager.get_relevant_memories("zylophonics", limit=1)
        assert len(top_1) == 1
        assert top_1[0]["importance"] == 9
    finally:
        for memory_id in ids:
            await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_edit_reembeds_on_content_change():
    memory_id = await memory_manager.save_memory(
        content=_unique_content("original unrelated sentence about weather"), importance=5
    )
    try:
        new_content = _unique_content("a totally different sentence about spacecraft propulsion")
        await memory_manager.update_memory(memory_id, content=new_content)

        hits = await vector_store.semantic_search(new_content, limit=5)
        assert any(h["id"] == memory_id for h in hits), (
            "Edited memory's embedding was not updated to reflect new content"
        )
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_delete_removes_embedding_no_orphan():
    content = _unique_content("a memory that will be deleted shortly")
    memory_id = await memory_manager.save_memory(content=content, importance=5)
    await memory_manager.delete_memory(memory_id)

    hits = await vector_store.semantic_search(content, limit=10)
    assert not any(h["id"] == memory_id for h in hits), (
        "Deleted memory's embedding is still present in ChromaDB (orphaned vector)"
    )


@pytest.mark.asyncio
async def test_migration_is_idempotent_and_backfills_missing():
    """Simulates a pre-existing memory that predates the embedding index
    (inserted directly, bypassing save_memory's auto-embed) and confirms
    migrate_embeddings() backfills it, then confirms a second run is a
    no-op (returns 0 newly-embedded)."""
    content = _unique_content("a legacy memory with no embedding yet")
    # Insert via save_memory (which embeds), then delete just the vector
    # to simulate "predates the embedding index" without touching SQLite.
    memory_id = await memory_manager.save_memory(content=content, importance=5)
    await vector_store.delete_memory(memory_id)

    pre_hits = await vector_store.semantic_search(content, limit=10)
    assert not any(h["id"] == memory_id for h in pre_hits)

    try:
        n_first = await memory_manager.migrate_embeddings()
        assert n_first >= 1

        post_hits = await vector_store.semantic_search(content, limit=10)
        assert any(h["id"] == memory_id for h in post_hits)

        n_second = await memory_manager.migrate_embeddings()
        assert n_second == 0, "Second migration run should not re-embed anything"
    finally:
        await memory_manager.delete_memory(memory_id)
