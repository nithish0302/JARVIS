from dataclasses import dataclass, field

from .credential_store import list_credential_keys


@dataclass
class PluginDefinition:
    id: str
    name: str
    description: str
    required_credentials: list[str] = field(default_factory=list)
    credential_namespace: str | None = None
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

    def resolve_namespace(self, plugin_id: str) -> str | None:
        """The credential-store namespace a plugin's secrets actually live
        under, or None if the plugin isn't registered.

        Most plugins store under their own id, but plugins that share one
        OAuth grant share a namespace: gmail and google_calendar both
        resolve to "google", because one consent screen issues the tokens
        for both.

        Every caller that touches the credential store for a plugin must
        go through here. This existed only inline inside is_configured(),
        so delete_plugin_credentials() passed the raw plugin_id straight
        to the store, looked for keys under "gmail" that were really under
        "google", found none, deleted nothing, and reported success.
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return None
        return plugin.credential_namespace or plugin_id

    def plugins_sharing_namespace(self, namespace: str) -> list[str]:
        """Ids of every registered plugin whose credentials live under
        `namespace` - i.e. everything affected by clearing it."""
        return [
            p.id
            for p in self.list_plugins()
            if self.resolve_namespace(p.id) == namespace
        ]

    def is_configured(self, plugin_id: str) -> bool:
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False
        if not plugin.required_credentials:
            return True
        ns = self.resolve_namespace(plugin_id)
        keys = list_credential_keys(ns)
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
