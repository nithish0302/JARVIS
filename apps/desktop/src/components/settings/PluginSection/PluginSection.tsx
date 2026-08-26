import { useState, useEffect } from "react";
import { Button } from "../../ui/Button/Button";

interface PluginInfo {
  id: string;
  name: string;
  description: string;
  is_configured: boolean;
}

export function PluginSection() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPlugins = async () => {
    try {
      const res = await fetch("http://localhost:8765/plugins");
      if (res.ok) {
        const data = await res.json();
        setPlugins(data);
      }
    } catch (err) {
      console.error("Failed to fetch plugins", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  const handleConnect = async (pluginId: string) => {
    if (pluginId === "gmail" || pluginId === "google_calendar") {
      try {
        const res = await fetch("http://localhost:8765/plugins/google/auth-url");
        if (res.ok) {
          const data = await res.json();
          const { open } = await import("@tauri-apps/plugin-shell");
          await open(data.url);
          // Poll for status update or rely on user to refresh
        }
      } catch (err) {
        console.error("Failed to fetch auth url", err);
      }
    } else {
      alert(`Connecting to ${pluginId} coming soon`);
    }
  };

  const handleDisconnect = async (pluginId: string) => {
    try {
      await fetch(`http://localhost:8765/plugins/${pluginId}/credentials`, {
        method: "DELETE",
      });
      fetchPlugins();
    } catch (err) {
      console.error("Failed to disconnect plugin", err);
    }
  };

  if (loading) {
    return <div className="p-6 text-[var(--color-text-secondary)]">Loading plugins...</div>;
  }

  return (
    <div className="flex flex-col gap-[var(--space-6)] p-6">
      <div className="flex flex-col gap-[var(--space-2)]">
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">
          Plugins
        </h2>
        <p className="text-[var(--color-text-secondary)]">
          Connect third-party services to extend JARVIS's capabilities.
        </p>
      </div>

      <div className="flex flex-col gap-[var(--space-4)]">
        {plugins.map((plugin) => (
          <div
            key={plugin.id}
            className="flex flex-col gap-[var(--space-4)] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-[var(--space-4)]"
          >
            <div className="flex items-start justify-between">
              <div className="flex flex-col gap-[var(--space-1)]">
                <div className="flex items-center gap-[var(--space-2)]">
                  <h3 className="text-base font-medium text-[var(--color-text-primary)]">
                    {plugin.name}
                  </h3>
                  {plugin.is_configured ? (
                    <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-500">
                      Connected
                    </span>
                  ) : (
                    <span className="rounded-full bg-[var(--color-surface-hover)] px-2 py-0.5 text-xs font-medium text-[var(--color-text-secondary)]">
                      Not connected
                    </span>
                  )}
                </div>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {plugin.description}
                </p>
              </div>
              <div>
                {plugin.is_configured ? (
                  <Button
                    variant="secondary"
                    onClick={() => handleDisconnect(plugin.id)}
                  >
                    Disconnect
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    onClick={() => handleConnect(plugin.id)}
                  >
                    Connect
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
