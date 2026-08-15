import "../../../styles/Panels.css";
import { Orb } from "../../orb/Orb/Orb";
import { cn } from "../../../lib/cn";

const HUBS = [
  { key: "skills", label: "Skills", color: "#5aa9e6", leaves: 9 },
  { key: "tools", label: "Tools", color: "#e85aa0", leaves: 6 },
  { key: "files", label: "Files", color: "#7a8c93", leaves: 8 },
  { key: "notes", label: "Notes", color: "#52d68a", leaves: 7 },
  { key: "worlds", label: "Worlds", color: "#e8934b", leaves: 5 },
  { key: "models", label: "Models", color: "#b98be8", leaves: 3 },
  { key: "conversations", label: "Conversations", color: "#ffb454", leaves: 0 },
];

export function RightColumn() {
  // In a real app this would read from the actual graph state
  const totalNodes = HUBS.length + HUBS.reduce((acc, h) => acc + h.leaves, 0);

  return (
    <div className="side-col shrink-0 flex flex-col h-full justify-between pb-3">
      <div className="panel flex-shrink min-h-0 flex flex-col !p-[10px_14px]">
        <h3 className="shrink-0">Filter</h3>
        <div className="overflow-y-auto no-scrollbar flex-1 grid grid-cols-2 gap-x-1 gap-y-[2px]">
          {HUBS.map((h) => (
            <div className={cn("legend-row !py-[2px] pr-1 text-[11px]", h.key === "conversations" && "col-span-2")} key={h.key} title={h.label}>
              <span className="sw flex-shrink-0" style={{ background: h.color }}></span>
              <span className="truncate">{h.label}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="flex-shrink-0">
        <Orb />
      </div>

      <div className="panel flex-shrink-0 !p-[10px_14px]">
        <h3>Graph</h3>
        <div className="flex gap-6 mt-1">
          <div className="flex items-baseline gap-[6px] text-[10px] font-semibold tracking-wider text-[var(--color-cyan)]">
            <b className="text-[14px] font-mono text-white">{totalNodes}</b>NODES
          </div>
          <div className="flex items-baseline gap-[6px] text-[10px] font-semibold tracking-wider text-[var(--color-cyan)]">
            <b className="text-[14px] font-mono text-white">{totalNodes}</b>LINKS
          </div>
        </div>
      </div>
    </div>
  );
}
