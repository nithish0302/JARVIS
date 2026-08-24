"""DELETE /conversation/{id} must enforce the same server-side PIN check
as DELETE /memories/{id} - previously it had none at all, so calling the
endpoint directly bypassed the frontend's PIN modal entirely."""
import uuid
import pytest
from starlette.testclient import TestClient

from jarvis_engine.main import app
from jarvis_engine.core.database import get_setting
from jarvis_engine.core.config import settings
from jarvis_engine.memory.conversation import save_message, get_conversation_messages


async def _make_conversation() -> str:
    conversation_id = f"test-conv-{uuid.uuid4().hex[:8]}"
    await save_message(conversation_id, "user", "hello")
    return conversation_id


@pytest.mark.asyncio
async def test_delete_conversation_rejected_without_valid_pin():
    conversation_id = await _make_conversation()
    try:
        with TestClient(app) as client:
            no_pin = client.delete(f"/conversation/{conversation_id}")
            wrong_pin = client.delete(f"/conversation/{conversation_id}", params={"pin": "0000"})
        assert no_pin.status_code == 403
        assert wrong_pin.status_code == 403

        # Still present - nothing was deleted.
        messages = await get_conversation_messages(conversation_id)
        assert len(messages) > 0
    finally:
        with TestClient(app) as client:
            stored_pin = await get_setting(
                "conversation_delete_pin", settings.CONVERSATION_DELETE_PIN
            )
            client.delete(f"/conversation/{conversation_id}", params={"pin": stored_pin})


@pytest.mark.asyncio
async def test_delete_conversation_succeeds_with_correct_pin():
    stored_pin = await get_setting(
        "conversation_delete_pin", settings.CONVERSATION_DELETE_PIN
    )
    conversation_id = await _make_conversation()

    with TestClient(app) as client:
        res = client.delete(f"/conversation/{conversation_id}", params={"pin": stored_pin})
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    messages = await get_conversation_messages(conversation_id)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_delete_conversation_404_for_unknown_id():
    stored_pin = await get_setting(
        "conversation_delete_pin", settings.CONVERSATION_DELETE_PIN
    )
    with TestClient(app) as client:
        res = client.delete("/conversation/does-not-exist", params={"pin": stored_pin})
    assert res.status_code == 404
