import "../../../styles/Panels.css";
import { Orb } from "../../orb/Orb/Orb";

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
    <div className="side-col max-lg:hidden overflow-y-auto pb-5 flex flex-col h-full gap-[14px]">
      <div className="panel flex-shrink-0 !p-[10px_14px]">
        <h3>Filter</h3>
        <div>
          {HUBS.map((h) => (
            <div className="legend-row !py-[2px]" key={h.key}>
              <span className="sw" style={{ background: h.color }}></span>
              {h.label}
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
