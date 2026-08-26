from pydantic import BaseModel
from typing import List
from ..plugins.registry import registry

class Capability(BaseModel):
    id: str
    name: str
    description: str
    category: str
    available: bool
    trigger: str

def get_all_capabilities() -> List[Capability]:
    caps = []
    
    # Built-in capabilities
    caps.extend([
        Capability(id="open_app", name="Open Application", description="Open desktop applications and browsers", category="automation", available=True, trigger="[UI_ACTION:OPEN_APP]"),
        Capability(id="system_control", name="System Control", description="Lock screen, close app, volume up/down/mute", category="automation", available=True, trigger="[UI_ACTION:SYSTEM_CONTROL]"),
        Capability(id="system_query", name="System Query", description="Check IP, battery, disk space, top processes, uptime, list_dir", category="system", available=True, trigger="[UI_ACTION:SYSTEM_QUERY]"),
        Capability(id="file_op", name="File Operations", description="Create folder, delete file, open file, show explorer", category="automation", available=True, trigger="[UI_ACTION:FILE_OP]"),
        
        Capability(id="chat_mode_on", name="Chat Mode On", description="Switch UI to chat mode", category="system", available=True, trigger="[UI_ACTION:chat_mode_on]"),
        Capability(id="chat_mode_off", name="Chat Mode Off", description="Switch UI to graph mode", category="system", available=True, trigger="[UI_ACTION:chat_mode_off]"),
        Capability(id="graph_open_hub", name="Open Hub", description="Open a specific UI hub (Skills/Tools/Files/Notes/Models/Conversations)", category="system", available=True, trigger="[UI_ACTION:graph_open_hub]"),
        Capability(id="conversations_open", name="Open Conversations", description="Open conversation panel", category="system", available=True, trigger="[UI_ACTION:conversations_open]"),
        Capability(id="provider_override", name="Lock Provider", description="Lock the AI provider", category="system", available=True, trigger="[UI_ACTION:provider_override]"),
        Capability(id="personality_mode", name="Switch Personality", description="Change AI personality", category="system", available=True, trigger="[UI_ACTION:personality_mode]"),
        Capability(id="modifier", name="Modifier Mode", description="Set quiet or planner mode", category="system", available=True, trigger="[UI_ACTION:modifier]"),
        Capability(id="address_preference", name="Address Preference", description="Set user address name", category="system", available=True, trigger="[UI_ACTION:address_preference]"),
        Capability(id="new_chat", name="New Chat", description="Start a new chat", category="system", available=True, trigger="[UI_ACTION:new_chat]"),
    ])
    
    # Plugin capabilities
    for p in registry.list_plugins():
        is_avail = registry.is_configured(p.id)
        for i, cap in enumerate(p.capabilities):
            trigger = p.ui_actions[i] if i < len(p.ui_actions) else ""
            caps.append(
                Capability(
                    id=f"{p.id}_{i}",
                    name=cap,
                    description=f"{p.name}: {p.description}",
                    category="plugin",
                    available=is_avail,
                    trigger=trigger
                )
            )
            
    return caps
