import "../../../styles/Panels.css";
import { Orb } from "../../orb/Orb/Orb";
import { cn } from "../../../lib/cn";
import { GRAPH_HUBS as HUBS } from "../../../data/graphHubs";

export function RightColumn() {
  // In a real app this would read from the actual graph state
  const totalNodes = HUBS.length + HUBS.reduce((acc, h) => acc + h.leaves, 0);

  return (
    <div
      className="side-col shrink-0 flex flex-col h-full"
      style={{
        width: "var(--right-col-width)",
        minWidth: "var(--right-col-width)"
      }}
    >
      <div className="flex-1 min-h-0 overflow-y-auto no-scrollbar flex flex-col gap-1 pb-1">
        <div className="panel flex-shrink-0 flex flex-col !p-[6px_14px] filter-panel">
          <h3 className="shrink-0">Filter</h3>
          <div className="grid grid-cols-2 gap-x-1 gap-y-[2px]">
            {HUBS.map((h) => (
              <div className={cn("legend-row !py-[2px] pr-1 text-[11px]", h.key === "conversations" && "col-span-2")} key={h.key} title={h.label}>
                <span className="sw flex-shrink-0" style={{ background: h.color }}></span>
                <span className="truncate">{h.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center justify-center">
          <Orb />
        </div>

        <div className="panel flex-shrink-0 !p-[6px_14px]">
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
    </div>
  );
}
