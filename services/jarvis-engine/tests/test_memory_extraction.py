import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from jarvis_engine.memory.memory_manager import memory_manager

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
async def test_genuine_memory_saved():
    """Verify 'i am a developer building JARVIS with Tauri' is recognized and saved as memory."""
    await asyncio.sleep(0.5)  # Avoid TPM rate limit spikes in tests
    msg = "i am a developer building JARVIS with Tauri"
    saved = await memory_manager.extract_and_save_memories(msg, "test-conv-3")
    print(f"\n[TEST 3] Genuine memory '{msg}' -> Saved: {saved}")
    assert len(saved) == 1, f"Expected 1 saved memory, got {saved}"
    assert any(term in saved[0].lower() for term in ["developer", "jarvis", "tauri"]), f"Unexpected saved content: {saved[0]}"

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
