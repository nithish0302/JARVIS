import "./CapabilitiesDashboard.css";
import { useEffect, useState } from "react";
import { getCapabilities } from "../../services/jarvisApi";
import { useAppStore } from "../../stores/useAppStore";

// Icons
const IconAutomation = () => (
  <svg className="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

const IconSystem = () => (
  <svg className="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
    <rect x="9" y="9" width="6" height="6" />
    <line x1="9" y1="1" x2="9" y2="4" />
    <line x1="15" y1="1" x2="15" y2="4" />
    <line x1="9" y1="20" x2="9" y2="23" />
    <line x1="15" y1="20" x2="15" y2="23" />
    <line x1="20" y1="9" x2="23" y2="9" />
    <line x1="20" y1="14" x2="23" y2="14" />
    <line x1="1" y1="9" x2="4" y2="9" />
    <line x1="1" y1="14" x2="4" y2="14" />
  </svg>
);

const IconPlugin = () => (
  <svg className="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22v-5" />
    <path d="M9 8V2" />
    <path d="M15 8V2" />
    <path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z" />
  </svg>
);

const getCategoryIcon = (category: string) => {
  switch (category.toLowerCase()) {
    case 'automation': return <IconAutomation />;
    case 'system': return <IconSystem />;
    case 'plugin': return <IconPlugin />;
    default: return null;
  }
};

type CapLayout = "a" | "b" | "c";

export function CapabilitiesDashboard() {
  const [capabilities, setCapabilities] = useState<any[]>([]);
  const [layout, setLayout] = useState<CapLayout>("a");
  const setView = useAppStore((state) => state.setView);

  useEffect(() => {
    getCapabilities().then(setCapabilities).catch(console.error);
  }, []);

  const categorized = capabilities.reduce((acc, cap) => {
    acc[cap.category] = acc[cap.category] || [];
    acc[cap.category].push(cap);
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div className="w-full h-full bg-[#030812] text-white p-8 pr-[calc(var(--dock-width)+2rem)] overflow-y-auto font-mono">
      <div className="mb-8">
        <h2 className="text-xl font-bold text-[var(--color-cyan)] tracking-wide">System Capabilities</h2>
        <div className="text-xs text-gray-400 mt-2 tracking-widest uppercase opacity-60">Registry of available commands and plugins</div>
      </div>

      <div className="layout-switcher">
        {(["a", "b", "c"] as CapLayout[]).map((key) => (
          <button
            key={key}
            className={`layout-switcher-btn ${layout === key ? "active" : ""}`}
            onClick={() => setLayout(key)}
          >
            Layout {key.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-10">
        {Object.entries(categorized).map(([category, caps]) => (
          <div key={category}>
            <div className={`category-header ${category.toLowerCase()} flex items-center gap-2`}>
              {getCategoryIcon(category)}
              <span>{category}</span>
            </div>

            <div className={`cap-grid-${layout}`}>
              {(caps as any[]).map((cap: any) => (
                <div key={cap.id} className={`capability-card p-4 rounded-lg flex flex-col gap-2 ${!cap.available ? 'unavailable' : ''}`}>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className={`status-dot ${cap.available ? 'available' : 'unavailable'}`} />
                      <span className="font-bold text-gray-200 text-sm tracking-wide">{cap.name}</span>
                    </div>
                    {!cap.available && cap.category === "plugin" && (
                      <button
                        onClick={() => setView("settings")}
                        className="text-xs text-[var(--color-cyan)] hover:underline px-2 py-1 bg-cyan-900/30 rounded border border-cyan-800/50 hover:bg-cyan-900/50 transition-colors tracking-wide"
                      >
                        Connect
                      </button>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 ml-5 leading-relaxed opacity-80">{cap.description}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
