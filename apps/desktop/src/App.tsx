import { ChatView } from "./components/chat/ChatView/ChatView";
import { AppShell } from "./components/layout/AppShell";
import { LayoutProvider } from "./components/layout/LayoutProvider";

function App() {
  return (
    <LayoutProvider>
      <AppShell>
        <ChatView />
      </AppShell>
    </LayoutProvider>
  );
}

export default App;
