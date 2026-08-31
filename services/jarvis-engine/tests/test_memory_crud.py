"""Phase 7 M2+M4: full memory CRUD (GET/PUT/DELETE), PIN-gated delete, and
importance-weighted retrieval ranking in get_relevant_memories()."""

import uuid

import pytest
from starlette.testclient import TestClient

from jarvis_engine.core.config import settings
from jarvis_engine.core.database import get_setting
from jarvis_engine.main import app
from jarvis_engine.memory.memory_manager import memory_manager


def _unique_content(label: str) -> str:
    # Unique per test run so it never collides with save_memory's
    # duplicate-content dedup check (matches on the first 100 chars).
    return f"[test-{uuid.uuid4().hex[:8]}] {label}"


@pytest.mark.asyncio
async def test_get_memories_returns_full_records():
    """GET /memories must return full records (id, content, category,
    importance, created_at, source_conversation_id), not just a count."""
    memory_id = await memory_manager.save_memory(
        content=_unique_content("full record shape check"),
        category="fact",
        importance=7,
        source_conversation_id="conv-shape-test",
    )
    try:
        with TestClient(app) as client:
            res = client.get("/memories")
        assert res.status_code == 200
        records = res.json()
        assert isinstance(records, list)

        match = next((r for r in records if r["id"] == memory_id), None)
        assert match is not None, "Newly saved memory not present in GET /memories"
        for field in (
            "id",
            "content",
            "category",
            "importance",
            "created_at",
            "source_conversation_id",
        ):
            assert field in match, f"Missing field '{field}' in memory record"
        assert match["category"] == "fact"
        assert match["importance"] == 7
        assert match["source_conversation_id"] == "conv-shape-test"
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_put_memory_edits_and_persists():
    """PUT /memories/{id} edits content/category/importance and the change
    persists (survives a fresh read, not just the response echo)."""
    memory_id = await memory_manager.save_memory(
        content=_unique_content("original content"), category="general", importance=3
    )
    try:
        with TestClient(app) as client:
            res = client.put(
                f"/memories/{memory_id}",
                json={
                    "content": "Edited content",
                    "category": "project",
                    "importance": 9,
                },
            )
        assert res.status_code == 200
        body = res.json()
        assert body["content"] == "Edited content"
        assert body["category"] == "project"
        assert body["importance"] == 9

        # Persistence check: re-fetch independently of the PUT response.
        all_memories = await memory_manager.get_all_memories(limit=200)
        persisted = next(m for m in all_memories if m["id"] == memory_id)
        assert persisted["content"] == "Edited content"
        assert persisted["category"] == "project"
        assert persisted["importance"] == 9
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_put_memory_rejects_importance_out_of_range():
    memory_id = await memory_manager.save_memory(
        content=_unique_content("importance validation check"), importance=5
    )
    try:
        with TestClient(app) as client:
            too_high = client.put(f"/memories/{memory_id}", json={"importance": 11})
            too_low = client.put(f"/memories/{memory_id}", json={"importance": 0})
        assert too_high.status_code == 422
        assert too_low.status_code == 422

        # Rejected requests must not have changed the stored value.
        all_memories = await memory_manager.get_all_memories(limit=200)
        persisted = next(m for m in all_memories if m["id"] == memory_id)
        assert persisted["importance"] == 5
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_put_memory_404_for_unknown_id():
    with TestClient(app) as client:
        res = client.put("/memories/does-not-exist", json={"importance": 5})
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_memory_rejected_without_valid_pin():
    """Same server-side gate as conversation deletion's /settings/verify-pin:
    wrong or missing PIN must not delete anything."""
    memory_id = await memory_manager.save_memory(
        content=_unique_content("pin gate check - wrong pin")
    )
    try:
        with TestClient(app) as client:
            no_pin = client.delete(f"/memories/{memory_id}")
            wrong_pin = client.delete(f"/memories/{memory_id}", params={"pin": "0000"})
        assert no_pin.status_code == 403
        assert wrong_pin.status_code == 403

        # Still present - nothing was deleted.
        all_memories = await memory_manager.get_all_memories(limit=200)
        assert any(m["id"] == memory_id for m in all_memories)
    finally:
        await memory_manager.delete_memory(memory_id)


@pytest.mark.asyncio
async def test_delete_memory_succeeds_with_correct_pin():
    """The correct PIN, verified via the exact same stored
    conversation_delete_pin setting /settings/verify-pin reads, actually
    deletes the memory."""
    stored_pin = await get_setting(
        "conversation_delete_pin", settings.CONVERSATION_DELETE_PIN
    )
    memory_id = await memory_manager.save_memory(
        content=_unique_content("pin gate check - correct pin")
    )

    with TestClient(app) as client:
        # Sanity-check this PIN is genuinely the one /settings/verify-pin
        # accepts - i.e. this is the SAME check, not a coincidentally equal
        # separate value.
        verify_res = client.post("/settings/verify-pin", json={"pin": stored_pin})
        assert verify_res.json()["valid"] is True

        res = client.delete(f"/memories/{memory_id}", params={"pin": stored_pin})
    assert res.status_code == 200
    assert res.json()["deleted"] is True

    all_memories = await memory_manager.get_all_memories(limit=200)
    assert not any(m["id"] == memory_id for m in all_memories)


@pytest.mark.asyncio
async def test_delete_memory_404_for_unknown_id():
    stored_pin = await get_setting(
        "conversation_delete_pin", settings.CONVERSATION_DELETE_PIN
    )
    with TestClient(app) as client:
        res = client.delete("/memories/does-not-exist", params={"pin": stored_pin})
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_relevant_memories_favors_higher_importance():
    """Concrete before/after: 4 memories all match the query word
    'quasarnetics' (a made-up token so this test can't collide with real
    data), with importance 2, 9, 5, 8 in save order (so recency alone would
    favor the LAST-saved, lowest-importance one). Asking for the top 2 must
    return the two highest-importance memories (9 and 8), not the two most
    recently saved (5 and 8)."""
    ids = []
    try:
        ids.append(
            await memory_manager.save_memory(
                content=_unique_content("quasarnetics low importance A"), importance=2
            )
        )
        ids.append(
            await memory_manager.save_memory(
                content=_unique_content("quasarnetics high importance A"), importance=9
            )
        )
        ids.append(
            await memory_manager.save_memory(
                content=_unique_content("quasarnetics mid importance"), importance=5
            )
        )
        # Saved LAST (most recent) but still lower importance than the 9 -
        # a pure-recency ranking would incorrectly place this above the 9.
        ids.append(
            await memory_manager.save_memory(
                content=_unique_content("quasarnetics high importance B"), importance=8
            )
        )

        top_2 = await memory_manager.get_relevant_memories("quasarnetics", limit=2)
        assert len(top_2) == 2
        top_2_importances = sorted(m["importance"] for m in top_2)
        assert top_2_importances == [8, 9], (
            f"Expected the two highest-importance memories (8, 9) to win, "
            f"got importances {[m['importance'] for m in top_2]} "
            f"(most-recent-first would have wrongly returned [8, 5])"
        )
    finally:
        for memory_id in ids:
            await memory_manager.delete_memory(memory_id)
