from dataclasses import dataclass, field
from .credential_store import list_credential_keys

@dataclass
class PluginDefinition:
    id: str
    name: str
    description: str
    required_credentials: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    ui_actions: list[str] = field(default_factory=list)
    is_enabled: bool = True

class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginDefinition] = {}

    def register(self, plugin: PluginDefinition):
        self._plugins[plugin.id] = plugin

    def get_plugin(self, plugin_id: str) -> PluginDefinition | None:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[PluginDefinition]:
        return list(self._plugins.values())

    def is_configured(self, plugin_id: str) -> bool:
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        if not plugin.required_credentials:
            return True
        keys = list_credential_keys(plugin_id)
        return all(req in keys for req in plugin.required_credentials)

    def get_capabilities_text(self) -> str:
        configured = [p for p in self.list_plugins() if self.is_configured(p.id)]
        if not configured:
            return ""
        
        lines = ["<PLUGIN_CAPABILITIES>"]
        for p in configured:
            lines.append(f"Plugin: {p.name}")
            if p.capabilities:
                lines.append("Capabilities:")
                for cap in p.capabilities:
                    lines.append(f"- {cap}")
            if p.ui_actions:
                lines.append("UI Actions:")
                for ui in p.ui_actions:
                    lines.append(f"- {ui}")
            lines.append("")
        lines.append("</PLUGIN_CAPABILITIES>")
        return "\n".join(lines)

registry = PluginRegistry()
