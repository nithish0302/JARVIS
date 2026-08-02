import { useState } from "react";
import { ChatView } from "./components/chat/ChatView/ChatView";
import { SettingsView } from "./components/settings/SettingsView/SettingsView";
import { AppShell } from "./components/layout/AppShell";
import { LayoutProvider } from "./components/layout/LayoutProvider";

function App() {
  const [view, setView] = useState<"chat" | "settings">("chat");

  return (
    <LayoutProvider>
      <AppShell
        onClose={view === "settings" ? () => setView("chat") : undefined}
        onSettingsOpen={view === "chat" ? () => setView("settings") : undefined}
      >
        {view === "chat" ? (
          <ChatView />
        ) : (
          <SettingsView />
        )}
      </AppShell>
    </LayoutProvider>
  );
}

export default App;
