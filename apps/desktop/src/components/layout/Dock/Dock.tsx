import "./Dock.css";
import { useAppStore } from "../../../stores/useAppStore";
import { cn } from "../../../lib/cn";
import { useState } from "react";

export function Dock() {
  const {
    graphOpen,
    setGraphOpen,
    conversationPanelOpen,
    setConversationPanelOpen,
    view,
    setView,
    chatMode,
    setChatMode,
  } = useAppStore();

  const [listening, setListening] = useState(false);

  return (
    <div className="dock">
      <div className="dock-mark">J</div>
      <button
        className={cn("dock-btn", graphOpen && "active")}
        title="Expand knowledge graph"
        onClick={() => setGraphOpen(!graphOpen)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <circle cx="6" cy="6" r="2.2" />
          <circle cx="18" cy="7" r="2.2" />
          <circle cx="7" cy="18" r="2.2" />
          <circle cx="17" cy="17" r="2.2" />
          <circle cx="12" cy="12" r="1.8" />
          <path d="M7.7 7.2 10.5 11M14 13 16.3 15.7M9.3 15.6 11 13.4M13.5 10.5 16 8" />
        </svg>
      </button>
      <button
        className={cn("dock-btn", conversationPanelOpen && "active")}
        title="Previous conversations"
        onClick={() => setConversationPanelOpen(true)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M4 5h16v11H8l-4 4V5Z" />
          <path d="M8 9h8M8 12h5" />
        </svg>
      </button>
      <button
        className={cn("dock-btn", chatMode && "active")}
        title="Toggle Chat Mode"
        onClick={() => setChatMode(!chatMode)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M4 5h16v11H8l-4 4V5Z" />
          <path d="M8 9h8M8 12h5" />
        </svg>
      </button>
      <button
        className={cn("dock-btn", view === "settings" && "active")}
        title="Settings"
        onClick={() => setView(view === "settings" ? "chat" : "settings")}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <circle cx="12" cy="12" r="2.6" />
          <path d="M12 3v2.4M12 18.6V21M21 12h-2.4M5.4 12H3M18 6l-1.6 1.6M7.6 16.4 6 18M18 18l-1.6-1.6M7.6 7.6 6 6" />
        </svg>
      </button>
      <div className="dock-spacer"></div>
      <button
        className={cn("dock-mic", listening && "live")}
        title="Toggle listening"
        onClick={() => setListening(!listening)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
          <rect x="9" y="3" width="6" height="11" rx="3" />
          <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
        </svg>
      </button>
    </div>
  );
}
