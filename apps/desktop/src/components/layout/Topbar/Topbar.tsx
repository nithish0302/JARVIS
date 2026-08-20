import "./Topbar.css";
import { useAIStore } from "../../../stores/useAIStore";
import { useAppStore } from "../../../stores/useAppStore";

export function Topbar() {
  const { provider, model, memoryCount, status } = useAIStore();
  const { graphMode, isCharging } = useAppStore();

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
