import "./Topbar.css";
import { useAIStore } from "../../../stores/useAIStore";

export function Topbar() {
  const { provider, model, memoryCount, status } = useAIStore();

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
        <div className="topbar-pill">
          <span className="pd"></span>
          {`${model} · ${provider}`}
        </div>
        <div className="topbar-pill amber">
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
