import "./Dock.css";
import { useAppStore } from "../../../stores/useAppStore";
import { useMicLevelStore } from "../../../stores/useMicLevelStore";
import { cn } from "../../../lib/cn";
import { startVoice, stopVoice } from "../../../services/jarvisApi";

export function Dock() {
  const graphOpen = useAppStore(state => state.graphOpen);
  const setGraphOpen = useAppStore(state => state.setGraphOpen);
  const conversationPanelOpen = useAppStore(state => state.conversationPanelOpen);
  const setConversationPanelOpen = useAppStore(state => state.setConversationPanelOpen);
  const view = useAppStore(state => state.view);
  const setView = useAppStore(state => state.setView);
  const voiceActive = useAppStore(state => state.voiceActive);
  const setVoiceActive = useAppStore(state => state.setVoiceActive);
  const micLevel = useMicLevelStore(state => state.level);

  // Amplitude-reactive glow ring: scales and brightens with the live mic
  // level. CSS transition on these props (see Dock.css) provides the
  // frame-to-frame easing; the exponential smoothing in useMicLevelStore
  // handles the value-to-value easing, so together the ring reads as a
  // smooth pulse rather than a jittery snap to each raw WS update.
  const ringScale = 1 + micLevel * 0.55;
  const ringOpacity = voiceActive ? 0.25 + micLevel * 0.65 : 0;

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

      <div className="dock-mic-wrap" style={{ position: 'absolute', bottom: '275px' }}>
        <span
          className="dock-mic-ring"
          style={{
            transform: `scale(${ringScale})`,
            opacity: ringOpacity,
          }}
        />
        <button
          className={cn("dock-mic", voiceActive && "live")}
          title={
            voiceActive
              ? "Listening — click to turn off. Glow pulses with live mic level."
              : "Click to start listening"
          }
          onClick={async () => {
            if (voiceActive) {
              await stopVoice();
              setVoiceActive(false);
            } else {
              await startVoice();
              setVoiceActive(true);
            }
          }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <rect x="9" y="3" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
          </svg>
        </button>
        {/* Persistent (not hover-only) cue that the glow is a live level
            meter, not just an on/off state — three bars that individually
            react to the same smoothed mic level as the ring, so it reads
            as "this measures something" rather than a static decoration. */}
        {voiceActive && (
          <div className="dock-mic-meter" aria-hidden="true" title="Live mic level">
            <span style={{ transform: `scaleY(${0.35 + micLevel * 1.4})` }} />
            <span style={{ transform: `scaleY(${0.5 + micLevel * 1.8})` }} />
            <span style={{ transform: `scaleY(${0.35 + micLevel * 1.4})` }} />
          </div>
        )}
      </div>
    </div>
  );
}
