import "./Dock.css";
import { useAppStore } from "../../../stores/useAppStore";
import { cn } from "../../../lib/cn";

export function Dock() {
  const graphOpen = useAppStore(state => state.graphOpen);
  const setGraphOpen = useAppStore(state => state.setGraphOpen);
  const conversationPanelOpen = useAppStore(state => state.conversationPanelOpen);
  const setConversationPanelOpen = useAppStore(state => state.setConversationPanelOpen);
  const view = useAppStore(state => state.view);
  const setView = useAppStore(state => state.setView);

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
          <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
        </svg>
      </button>
      
      <button
        className={cn("dock-btn", view === "settings" && "active")}
        title="Settings"
        onClick={() => setView(view === "settings" ? "chat" : "settings")}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z"/>
        </svg>
      </button>
    </div>
  );
}
