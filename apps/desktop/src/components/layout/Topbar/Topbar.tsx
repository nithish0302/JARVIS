import "./Topbar.css";
import { useAIStore } from "../../../stores/useAIStore";
import { useAppStore } from "../../../stores/useAppStore";
import { updateSettings } from "../../../services/jarvisApi";

export function Topbar() {
  const {
    provider,
    model,
    memoryCount,
    status,
    personalityMode,
    modifier,
    setPersonalityMode,
    setModifier
  } = useAIStore();
  const { graphMode, isCharging } = useAppStore();

  const handlePersonalityClick = async () => {
    const modes: Array<"assistant" | "developer" | "research"> = ["assistant", "developer", "research"];
    const currentIndex = modes.indexOf(personalityMode);
    const nextMode = modes[(currentIndex + 1) % modes.length];
    setPersonalityMode(nextMode);
    try {
      await updateSettings({ personality_mode: nextMode });
    } catch (err) {
      console.error("Failed to update personality mode:", err);
    }
  };

  const handleModifierClick = async () => {
    const modifiers: Array<"none" | "planner" | "quiet"> = ["none", "planner", "quiet"];
    const currentIndex = modifiers.indexOf(modifier);
    const nextModifier = modifiers[(currentIndex + 1) % modifiers.length];
    setModifier(nextModifier);
    try {
      await updateSettings({ modifier: nextModifier });
    } catch (err) {
      console.error("Failed to update modifier:", err);
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case "idle":
        return "IDLE";
      case "connecting":
        return "CONNECTING...";
      case "streaming":
        return "THINKING...";
      case "error":
        return "ERROR";
      case "offline":
        return "OFFLINE";
      default:
        return (status as string).toUpperCase();
    }
  };

  return (
    <div className="topbar">
      <div className="topbar-brand">
        <span className="dot"></span>J.A.R.V.I.S
      </div>
      <div className="topbar-pills">
        <button
          className="topbar-pill topbar-personality-pill"
          onClick={handlePersonalityClick}
          title={`Personality Mode: ${personalityMode.toUpperCase()} (click to switch)`}
          style={{ cursor: "pointer", background: "rgba(0, 240, 255, 0.05)" }}
        >
          <span className="pd" style={{
            background: personalityMode === "developer" ? "#a855f7" :
                        personalityMode === "research" ? "#10b981" :
                        "var(--color-cyan)"
          }}></span>
          {personalityMode.toUpperCase()}
          <span className="pill-affordance" aria-hidden="true">⟳</span>
        </button>

        <button
          className="topbar-pill topbar-modifier-pill"
          onClick={handleModifierClick}
          title={`Modifier: ${modifier.toUpperCase()} (click to cycle)`}
          style={{
            cursor: "pointer",
            borderColor: modifier === "planner" ? "rgba(245, 158, 11, 0.4)" : "rgba(148, 163, 184, 0.4)",
            color: modifier === "planner" ? "var(--color-amber)" : "var(--color-text-muted, #94a3b8)",
            background: "rgba(0,0,0,0.2)"
          }}
        >
          <span className="pd" style={{
            background: modifier === "planner" ? "var(--color-amber)" : "#94a3b8"
          }}></span>
          [{modifier.toUpperCase()}]
          <span className="pill-affordance" aria-hidden="true">⟳</span>
        </button>

        <div className="topbar-pill topbar-model-pill">
          <span className="pd"></span>
          {`${model} · ${provider}`}
        </div>
        <div className="topbar-mode-pill" style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
          padding: "2px 8px",
          background: "rgba(82,236,227,0.06)",
          border: "1px solid rgba(82,236,227,0.15)",
          borderRadius: "4px",
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          color: isCharging
            ? "var(--color-cyan)"
            : "var(--color-amber)",
          letterSpacing: "0.5px"
        }}>
          {isCharging ? "⚡" : "🔋"}
          &nbsp;
          {graphMode.toUpperCase()}
        </div>
        <div className="topbar-pill amber topbar-memory-pill">
          <span className="pd"></span>
          {memoryCount} MEMORIES
        </div>
        <div className="topbar-pill">
          <span className="pd"></span>
          {getStatusLabel()}
        </div>
      </div>
    </div>
  );
}
