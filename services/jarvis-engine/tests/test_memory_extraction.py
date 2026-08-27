import asyncio
import json
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import aiosqlite

from jarvis_engine.core.config import settings
from jarvis_engine.memory.memory_manager import memory_manager


async def _find_memory_id_by_content(content: str) -> str | None:
    """Direct DB lookup for test cleanup - extract_and_save_memories()
    only returns the saved content strings, not the row id, so this is
    how the mocked-LLM test below finds what it just wrote in order to
    remove it again."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM memories WHERE content = ?", (content,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


def _fake_groq_response(should_save: bool, content: str = "", category: str = "general", importance: int = 5):
    """Builds an object shaped like what extract_and_save_memories()
    reads off a real Groq response: resp.choices[0].message.content is a
    JSON string, exactly as the AsyncGroq SDK returns it.

    Uses json.dumps rather than %r/str formatting - %r produces Python's
    single-quoted repr, not valid JSON, which made extract_and_save_
    memories' json.loads() silently fail on the mocked response (caught
    by its own bare `except Exception: continue`), retry the second
    model, fail identically, and return should_save=False with no error
    surfaced anywhere. First-draft bug in this fix, caught by actually
    running the test rather than trusting the code once it looked right.
    """
    payload = json.dumps({
        "should_save": should_save,
        "content": content,
        "category": category,
        "importance": importance,
    })
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = payload
    return resp


@pytest.mark.asyncio
async def test_false_positive_doubt_rejected():
    """Verify 'i am not sure if the graph feature works' is rejected and not saved as memory."""
    msg = "i am not sure if the graph feature works"
    saved = await memory_manager.extract_and_save_memories(msg, "test-conv-1")
    print(f"\n[TEST 1] False positive doubt '{msg}' -> Saved: {saved}")
    assert len(saved) == 0, f"Expected 0 saved memories, got {saved}"

@pytest.mark.asyncio
async def test_false_positive_question_rejected():
    """Verify 'how do i use the graph feature' is rejected and not saved as memory."""
    await asyncio.sleep(0.5)  # Avoid TPM rate limit spikes in tests
    msg = "how do i use the graph feature"
    saved = await memory_manager.extract_and_save_memories(msg, "test-conv-2")
    print(f"\n[TEST 2] False positive question '{msg}' -> Saved: {saved}")
    assert len(saved) == 0, f"Expected 0 saved memories, got {saved}"

@pytest.mark.asyncio
async def test_genuine_memory_saved(monkeypatch):
    """save_memory() correctly persists a memory once the LLM has decided
    should_save=true.

    This used to call the real Groq model and assert on ITS judgment -
    that "i am a developer building JARVIS with Tauri" gets should_save:
    true. That re-tested the model's own decision on every run (subject
    to rate limiting and, on borderline phrasing, genuine
    non-determinism) rather than this function's actual job: given a
    should_save:true response, does it correctly persist the content,
    category and importance the model returned. That job is exercised
    identically whether the JSON came from a live call or this fixed
    stub, and the stub is what makes the test deterministic.

    Whether the real model still makes sensible should_save calls on
    real input is a legitimate thing to keep checking, but it belongs in
    a separate, clearly-labeled live/smoke test - not gating every run of
    this suite. None currently exists; see the audit note this test was
    fixed under for that gap.
    """
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")

    # Unique per run, same convention as test_memory_crud.py's
    # _unique_content(): a realistic-looking fixed string here collided
    # with save_memory()'s near-duplicate dedup (content_similarity >=
    # 0.85), which correctly matched it against 8 leftover memories this
    # exact test accumulated in the live DB across earlier, unmocked
    # runs - and updated one of THOSE rows instead of inserting this
    # content, so the "is it really in the DB" check below found nothing
    # under the new text. The marker keeps this run's content dissimilar
    # enough (~0.2 ratio, well under 0.85) to always take the insert path.
    marker = uuid.uuid4().hex[:8]
    fake_content = f"[test-{marker}] developer building JARVIS with Tauri"
    fake_response = _fake_groq_response(
        should_save=True,
        content=fake_content,
        category="project",
        importance=7,
    )

    with patch("groq.AsyncGroq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_response)
        mock_groq_cls.return_value = mock_client

        msg = "i am a developer building JARVIS with Tauri"
        saved = await memory_manager.extract_and_save_memories(msg, "test-conv-3")

    try:
        print(f"\n[TEST 3] Genuine memory (mocked LLM) -> Saved: {saved}")

        # The LLM was actually called - this isn't skipping extraction,
        # just fixing its output.
        mock_client.chat.completions.create.assert_awaited_once()

        assert len(saved) == 1, f"Expected 1 saved memory, got {saved}"
        assert saved[0] == fake_content, f"Unexpected saved content: {saved[0]}"

        # And it's really in the DB, not just returned - the actual thing
        # this test is responsible for verifying.
        memory_id = await _find_memory_id_by_content(fake_content)
        assert memory_id is not None, "Memory was reported saved but not found in the DB"
    finally:
        memory_id = await _find_memory_id_by_content(fake_content)
        if memory_id:
            await memory_manager.delete_memory(memory_id)

@pytest.mark.asyncio
async def test_groq_timeout_fallback_skips_saving():
    """Verify that if Groq call times out or throws, extraction safely skips saving."""
    with patch("groq.AsyncGroq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=TimeoutError("Request timed out"))
        mock_groq_cls.return_value = mock_client
        
        msg = "i am a developer building JARVIS with Tauri"
        saved = await memory_manager.extract_and_save_memories(msg, "test-conv-4")
        print(f"\n[TEST 4] Groq timeout fallback -> Saved: {saved}")
        assert len(saved) == 0, "Failed Groq call should safely skip saving"
