import pytest
import asyncio
from jarvis_engine.core.database import init_db, get_setting, set_setting
from jarvis_engine.api.routes import (
    get_system_prompt,
    PERSONALITY_ASSISTANT_PROMPT,
    PERSONALITY_DEVELOPER_PROMPT,
    PERSONALITY_RESEARCH_PROMPT,
    MODIFIER_PLANNER_PROMPT,
    MODIFIER_QUIET_PROMPT,
    get_settings_endpoint,
    update_settings_endpoint,
)

@pytest.mark.asyncio
async def test_personality_prompt_combinations():
    # 1. Base personality prompts without modifier
    p_asst = get_system_prompt("assistant", "none")
    assert "You are JARVIS, a premium AI desktop assistant" in p_asst
    assert "[MODIFIER:" not in p_asst

    p_dev = get_system_prompt("developer", "none")
    assert "Developer Mode" in p_dev
    assert "Technical precision over warmth" in p_dev
    assert "[MODIFIER:" not in p_dev

    p_res = get_system_prompt("research", "none")
    assert "Research Mode" in p_res
    assert "Thorough, investigative, and exploratory" in p_res
    assert "[MODIFIER:" not in p_res

    # 2. Modifiers combined with personality
    p_asst_planner = get_system_prompt("assistant", "planner")
    assert "You are JARVIS, a premium AI desktop assistant" in p_asst_planner
    assert "[MODIFIER: PLANNER ACTIVE]" in p_asst_planner

    p_dev_quiet = get_system_prompt("developer", "quiet")
    assert "Developer Mode" in p_dev_quiet
    assert "[MODIFIER: QUIET ACTIVE]" in p_dev_quiet

    p_res_planner = get_system_prompt("research", "planner")
    assert "Research Mode" in p_res_planner
    assert "[MODIFIER: PLANNER ACTIVE]" in p_res_planner

    # 3. Fallbacks on invalid input
    p_fallback = get_system_prompt("unknown_mode", "unknown_mod")
    assert "You are JARVIS, a premium AI desktop assistant" in p_fallback
    assert "[MODIFIER:" not in p_fallback

@pytest.mark.asyncio
async def test_settings_persistence_and_endpoints():
    await init_db()

    # Initial update via endpoint
    res1 = await update_settings_endpoint({"personality_mode": "developer", "modifier": "planner"})
    assert res1["personality_mode"] == "developer"
    assert res1["modifier"] == "planner"

    # Verify retrieval
    res_get = await get_settings_endpoint()
    assert res_get["personality_mode"] == "developer"
    assert res_get["modifier"] == "planner"

    # Verify direct DB function
    db_mode = await get_setting("personality_mode")
    db_mod = await get_setting("modifier")
    assert db_mode == "developer"
    assert db_mod == "planner"

    # Update modifier to quiet
    res2 = await update_settings_endpoint({"modifier": "quiet"})
    assert res2["personality_mode"] == "developer"
    assert res2["modifier"] == "quiet"

    # Reset back to assistant / none
    res3 = await update_settings_endpoint({"personality_mode": "assistant", "modifier": "none"})
    assert res3["personality_mode"] == "assistant"
    assert res3["modifier"] == "none"
