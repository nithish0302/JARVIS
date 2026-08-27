"""Tests for voice/chat parity gaps and voice session conversation continuity."""

import pytest
import uuid
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from jarvis_engine.api.routes import router
from jarvis_engine.core.config import settings
from jarvis_engine.memory.memory_manager import memory_manager
from jarvis_engine.memory.conversation import get_conversation_messages, get_conversations
from jarvis_engine.voice.voice_manager import VoiceManager
import jarvis_engine.voice.transcription_handler as th
import aiosqlite


@pytest.mark.asyncio
async def test_voice_input_persists_messages_and_uses_conversation_id(monkeypatch):
    """Parity Gap 2: voice turns must be persisted to conversations/messages tables."""
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    async def fake_cascade(messages, user_text, providers):
        return {
            "status": "ok",
            "response_text": "Hello there!",
            "provider_used": "mock",
            "model_used": "mock-model",
            "fallback_occurred": False,
            "failed_provider": None,
        }

    monkeypatch.setattr("jarvis_engine.api.routes.run_cascade", fake_cascade)

    cid = str(uuid.uuid4())
    res = client.post("/voice/input", json={"text": "hello jarvis", "conversation_id": cid})
    assert res.status_code == 200
    data = res.json()
    assert data["conversation_id"] == cid

    # Verify messages in DB
    msgs = await get_conversation_messages(cid)
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[0].content == "hello jarvis"
    assert msgs[1].role == "assistant"
    assert "Hello there!" in msgs[1].content


@pytest.mark.asyncio
async def test_voice_input_memory_context_injection(monkeypatch):
    """Parity Gap 1: get_relevant_memories must be injected into prompt."""
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # Save a test memory
    mem_id = await memory_manager.save_memory("Nithish prefers dark roast coffee", importance=8)

    captured_messages = []

    async def fake_cascade(messages, user_text, providers):
        captured_messages.extend(messages)
        return {
            "status": "ok",
            "response_text": "Dark roast coffee noted.",
            "provider_used": "mock",
            "model_used": "mock-model",
            "fallback_occurred": False,
            "failed_provider": None,
        }

    monkeypatch.setattr("jarvis_engine.api.routes.run_cascade", fake_cascade)

    res = client.post("/voice/input", json={"text": "what coffee do I prefer?"})
    assert res.status_code == 200

    # System prompt should contain memory context
    system_prompt = captured_messages[0].content
    assert "Relevant memories about Nithish:" in system_prompt
    assert "dark roast coffee" in system_prompt


@pytest.mark.asyncio
async def test_voice_input_memory_extraction(monkeypatch):
    """Parity Gap 3: extract_and_save_memories must be called on voice turn."""
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    async def fake_cascade(messages, user_text, providers):
        return {
            "status": "ok",
            "response_text": "That is good to know.",
            "provider_used": "mock",
            "model_used": "mock-model",
            "fallback_occurred": False,
            "failed_provider": None,
        }

    extracted_calls = []

    async def fake_extract(text, conversation_id=None):
        extracted_calls.append((text, conversation_id))

    monkeypatch.setattr("jarvis_engine.api.routes.run_cascade", fake_cascade)
    monkeypatch.setattr(memory_manager, "extract_and_save_memories", fake_extract)

    cid = str(uuid.uuid4())
    res = client.post("/voice/input", json={"text": "I like dark roast coffee", "conversation_id": cid})
    assert res.status_code == 200

    assert len(extracted_calls) == 1
    assert extracted_calls[0] == ("I like dark roast coffee", cid)


@pytest.mark.asyncio
async def test_voice_input_gap_logging(monkeypatch):
    """Parity Gap 4: detect_and_log_gap must fire on voice capability gaps."""
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    async def fake_cascade(messages, user_text, providers):
        return {
            "status": "ok",
            "response_text": "I can't book a flight for you right now.",
            "provider_used": "mock",
            "model_used": "mock-model",
            "fallback_occurred": False,
            "failed_provider": None,
        }

    monkeypatch.setattr("jarvis_engine.api.routes.run_cascade", fake_cascade)

    request_text = f"book me a flight {uuid.uuid4()}"
    res = client.post("/voice/input", json={"text": request_text})
    assert res.status_code == 200

    # Verify entry in gap_log table
    async with aiosqlite.connect(settings.DB_PATH) as db:
        async with db.execute(
            "SELECT user_request, gap_reason FROM gap_log WHERE user_request = ?",
            (request_text,)
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == request_text
            assert "I can't book a flight" in row[1]


@pytest.mark.asyncio
async def test_voice_input_preserves_ui_action_instruction_with_automation(monkeypatch):
    """Parity Gap 5: UI_ACTION_INSTRUCTION must not be dropped when automation is detected."""
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    captured_messages = []

    async def fake_cascade(messages, user_text, providers):
        captured_messages.extend(messages)
        return {
            "status": "ok",
            "response_text": "Opening notepad. [UI_ACTION:open_app:notepad.exe]",
            "provider_used": "mock",
            "model_used": "mock-model",
            "fallback_occurred": False,
            "failed_provider": None,
        }

    monkeypatch.setattr("jarvis_engine.api.routes.run_cascade", fake_cascade)
    monkeypatch.setattr("jarvis_engine.api.routes.is_file_system_command", lambda t: (True, {"action": "open_app", "path": "notepad.exe"}))

    res = client.post("/voice/input", json={"text": "open notepad"})
    assert res.status_code == 200

    system_content = captured_messages[0].content
    # Both UI_ACTION_INSTRUCTION and file system / automation context must be present
    assert "[UI_ACTION:" in system_content
    assert "[FILE SYSTEM COMMAND DETECTED]" in system_content


def test_voice_manager_session_conversation_id():
    """Verify VoiceManager maintains session conversation_id across continuous turns."""
    vm = VoiceManager()
    assert vm.conversation_id is None

    # Start listening cycle assigns a conversation_id
    with patch.object(vm, "_process_voice_command"):
        vm._start_listening_cycle()
        assert vm.conversation_id is not None
        session_cid = vm.conversation_id

    # Continuing conversation in same session retains conversation_id
    vm.continue_conversation()
    assert vm.conversation_id == session_cid

    # Exiting continuous mode clears conversation_id
    vm._exit_continuous_mode()
    assert vm.conversation_id is None
