import { useState } from "react";
import { ChatView } from "./components/chat/ChatView/ChatView";
import { SettingsView } from "./components/settings/SettingsView/SettingsView";
import { AppShell } from "./components/layout/AppShell";
import { LayoutProvider } from "./components/layout/LayoutProvider";
import { AnimatePresence, motion, useReducedMotion, easeInOut } from "framer-motion";

function App() {
  const [view, setView] = useState<"chat" | "settings">("chat");
  const shouldReduceMotion = useReducedMotion();
  const transition = { duration: shouldReduceMotion ? 0 : 0.25, ease: easeInOut };

  return (
    <LayoutProvider>
      <AppShell
        onClose={view === "settings" ? () => setView("chat") : undefined}
        onSettingsOpen={view === "chat" ? () => setView("settings") : undefined}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            animate={{ opacity: 1 }}
            className="flex h-full w-full flex-col min-h-0"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            transition={transition}
          >
            {view === "chat" ? <ChatView /> : <SettingsView />}
          </motion.div>
        </AnimatePresence>
      </AppShell>
    </LayoutProvider>
  );
}

export default App;
