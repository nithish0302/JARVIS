import { SettingsView } from "./components/settings/SettingsView/SettingsView";
import { LayoutProvider } from "./components/layout/LayoutProvider";
import { AnimatePresence, motion, useReducedMotion, easeInOut } from "framer-motion";
import { useAppStore } from "./stores/useAppStore";
import { useEngineStatus } from "./hooks/useEngineStatus";
import { useConversationLoader } from "./hooks/useConversationLoader";
import { usePowerMode } from "./hooks/usePowerMode";
import { useGlobalShortcuts } from "./hooks/useGlobalShortcuts";

// New HUD Components
import { Stage, Scene } from "./components/layout/Stage/Stage";
import { Topbar } from "./components/layout/Topbar/Topbar";
import { LeftColumn } from "./components/layout/LeftColumn/LeftColumn";
import { RightColumn } from "./components/layout/RightColumn/RightColumn";
import { GraphCanvas } from "./components/graph/GraphCanvas/GraphCanvas";
import { ChatShell } from "./components/chat/ChatShell/ChatShell";
import { Dock } from "./components/layout/Dock/Dock";
import { ConversationPanel } from "./components/conversations/ConversationPanel/ConversationPanel";
import { ChatFullView } from "./components/chat/ChatFullView/ChatFullView";
import { CommandPalette } from "./components/palette/CommandPalette/CommandPalette";
import { ShortcutToast } from "./components/layout/ShortcutToast/ShortcutToast";
import { FallbackToast } from "./components/layout/FallbackToast/FallbackToast";
import { GapDashboard } from "./components/gaps/GapDashboard";

function App() {
  const view = useAppStore((state) => state.view);
  const chatMode = useAppStore((state) => state.chatMode);
  const shouldReduceMotion = useReducedMotion();
  const transition = { duration: shouldReduceMotion ? 0 : 0.25, ease: easeInOut };

  useEngineStatus();
  useConversationLoader();
  usePowerMode();
  // Registered here at the composition root so shortcuts fire regardless
  // of which panel currently holds focus.
  useGlobalShortcuts();

  return (
    <LayoutProvider>
      <AnimatePresence mode="wait">
        <motion.div
          key={view}
          animate={{ opacity: 1 }}
          className="flex h-full w-full flex-row overflow-hidden"
          exit={{ opacity: 0 }}
          initial={{ opacity: 0 }}
          transition={transition}
        >
          {view === "chat" ? (
            <>
              <Stage>
                <Topbar />
                {chatMode ? (
                  <Scene className="chat-mode">
                    <LeftColumn />
                    <ChatFullView />
                    <RightColumn />
                  </Scene>
                ) : (
                  <>
                    <Scene>
                      <LeftColumn />
                      <GraphCanvas />
                      <RightColumn />
                    </Scene>
                    <ChatShell />
                  </>
                )}
              </Stage>
              <Dock />
              <ConversationPanel />
            </>
          ) : view === "gaps" ? (
            <div className="w-full h-full flex flex-col relative">
              <GapDashboard />
              <div className="absolute top-4 right-4 z-50">
                <Dock />
              </div>
            </div>
          ) : (
            <div className="w-full h-full flex flex-col relative">
              <SettingsView />
              <div className="absolute top-4 right-4 z-50">
                <Dock />
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
      {/* Rendered outside the view switch so both are available from the
          chat/graph view and the settings view alike. */}
      <CommandPalette />
      <ShortcutToast />
      <FallbackToast />
    </LayoutProvider>
  );
}

export default App;
