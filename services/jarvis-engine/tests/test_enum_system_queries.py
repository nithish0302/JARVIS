import pytest
from jarvis_engine.api.routes import get_automation_context_str, needs_automation
from jarvis_engine.voice.voice_manager import _execute_action

@pytest.mark.asyncio
async def test_get_automation_context_system_queries():
    # Test IP query
    results_ip = [{"action_type": "SYSTEM_QUERY", "command": "ip_address", "description": "Get IP"}]
    ctx_ip = await get_automation_context_str(results_ip)
    assert "[UI_ACTION:system_query:ip_address]" in ctx_ip
    assert "powershell" not in ctx_ip.lower()

    # Test top processes
    results_proc = [{"action_type": "SYSTEM_QUERY", "command": "top_processes", "description": "Top processes"}]
    ctx_proc = await get_automation_context_str(results_proc)
    assert "[UI_ACTION:system_query:top_processes]" in ctx_proc
    assert "powershell" not in ctx_proc.lower()

    # Test battery
    results_bat = [{"action_type": "SYSTEM_QUERY", "command": "battery_level", "description": "Battery"}]
    ctx_bat = await get_automation_context_str(results_bat)
    assert "[UI_ACTION:system_query:battery_level]" in ctx_bat
    assert "powershell" not in ctx_bat.lower()

    # Test disk
    results_disk = [{"action_type": "SYSTEM_QUERY", "command": "disk_space", "description": "Disk"}]
    ctx_disk = await get_automation_context_str(results_disk)
    assert "[UI_ACTION:system_query:disk_space]" in ctx_disk
    assert "powershell" not in ctx_disk.lower()

@pytest.mark.asyncio
async def test_get_automation_context_mutative_actions():
    # Test close app
    results_close = [{"action_type": "SYSTEM_CONTROL", "command": "close_app:notepad", "description": "Close Notepad"}]
    ctx_close = await get_automation_context_str(results_close)
    assert "[UI_ACTION:close_app:notepad]" in ctx_close

    # Test volume
    results_vol = [{"action_type": "SYSTEM_CONTROL", "command": "volume_up", "description": "Volume Up"}]
    ctx_vol = await get_automation_context_str(results_vol)
    assert "[UI_ACTION:set_volume:up]" in ctx_vol

def test_voice_manager_direct_actions_no_powershell():
    # Test volume action execution via Win32 keybd_event
    res_up = _execute_action("volume", "up")
    assert res_up == "Volume up, sir."

    res_down = _execute_action("volume", "down")
    assert res_down == "Volume down, sir."

    # Test system queries
    res_time = _execute_action("system_query", "time")
    assert "The time is" in res_time

    res_ip = _execute_action("system_query", "ip")
    assert "Your IP is" in res_ip
