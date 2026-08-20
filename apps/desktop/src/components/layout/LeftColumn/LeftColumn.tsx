import { useEffect, useState } from "react";
import "../../../styles/Panels.css";
import { useAppStore } from "../../../stores/useAppStore";
import { cn } from "../../../lib/cn";
import { invoke } from "@tauri-apps/api/core";

export function LeftColumn() {
  const graphOpen = useAppStore(state => state.graphOpen);
  const activeHub = useAppStore(state => state.activeHub);
  const chatMode = useAppStore(state => state.chatMode);
  const setChatMode = useAppStore(state => state.setChatMode);
  const inspectorMessage = useAppStore(state => state.inspectorMessage);

  const [cpuUsage, setCpuUsage] = useState(0);
  const [cpuName, setCpuName] = useState("Unknown CPU");
  const [cpuCores, setCpuCores] = useState(0);
  const [ramPct, setRamPct] = useState(0);
  const [ramUsed, setRamUsed] = useState("0");
  const [ramTotal, setRamTotal] = useState("0");
  const [gpus, setGpus] = useState<any[]>([]);
  const [batteryLevel, setBatteryLevel] = useState(100);
  const [batteryStatus, setBatteryStatus] = useState("Unknown");
  const [diskPct, setDiskPct] = useState(0);
  const [diskUsed, setDiskUsed] = useState("0");
  const [diskTotal, setDiskTotal] = useState("0");

  useEffect(() => {
    let mounted = true;
    const fetchStats = async () => {
      try {
        if (!('__TAURI_INTERNALS__' in window)) return;
        const stats = await invoke<any>("get_system_info");
        if (!mounted) return;
        setCpuUsage(stats.cpu_usage);
        setCpuName(stats.cpu_name);
        setCpuCores(stats.cpu_cores);
        setRamPct(stats.ram_pct);
        setRamUsed(stats.ram_used_gb);
        setRamTotal(stats.ram_total_gb);
        setGpus(stats.gpus);
      } catch (e) {
        console.error("Failed to fetch system info", e);
      }
    };

    const fetchLongStats = async () => {
      try {
        if (!('__TAURI_INTERNALS__' in window)) return;
        const [batt, disk] = await Promise.all([
          invoke<any>("get_battery_info"),
          invoke<any>("get_disk_info")
        ]);
        if (!mounted) return;
        setBatteryLevel(batt.level);
        setBatteryStatus(batt.status);
        setDiskPct(disk.pct);
        setDiskUsed(disk.used_gb);
        setDiskTotal(disk.total_gb);
      } catch (e) {
        console.error("Failed to fetch long stats", e);
      }
    };

    fetchStats();
    fetchLongStats();
    const interval = setInterval(fetchStats, 3000);
    const longInterval = setInterval(fetchLongStats, 60000);
    return () => {
      mounted = false;
      clearInterval(interval);
      clearInterval(longInterval);
    };
  }, []);

  const renderInspectorContent = () => {
    if (activeHub === "conversations") {
      return (
        <>
          <div className="node-title">Conversations</div>
          <div className="node-meta">HISTORY</div>
          <div className="node-desc">
            Every past session lives here. Panel opened on the right — click any entry to reload that transcript.
          </div>
        </>
      );
    }
    if (activeHub) {
      return (
        <>
          <div className="node-title">{activeHub.charAt(0).toUpperCase() + activeHub.slice(1)}</div>
          <div className="node-meta">{activeHub.toUpperCase()}</div>
          <div className="node-desc">
            Wire this up to your real note/embedding store — summary, source file, last-updated time.
          </div>
        </>
      );
    }
    if (graphOpen) {
      return (
        <div className="inspector-empty">
          Full graph — click any node to inspect it, or click the center again to close.
        </div>
      );
    }
    return (
      <div className="inspector-empty">
        Click any node — the gold one is your conversation history. Everything else is your connected knowledge.
      </div>
    );
  };

  return (
    <div
      className="side-col shrink-0 flex-col h-full"
      style={{
        width: "var(--left-col-width)",
        minWidth: "var(--left-col-width)"
      }}
    >
      <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-[14px] pb-4">
      <div className={cn("panel", activeHub ? "flex-[0_0_auto]" : "flex-[0_0_auto]")} id="inspector">
        <h3 className="flex items-center justify-between">
          Inspector
          <span className="text-[10px] text-[var(--color-cyan)] opacity-70">
            {activeHub ? "▼" : "▶"}
          </span>
        </h3>
        {activeHub ? (
          renderInspectorContent()
        ) : inspectorMessage ? (
          <div className="text-[11px] text-[var(--color-cyan)] mt-1 font-mono uppercase">
            ● {inspectorMessage}
          </div>
        ) : (
          <div className="text-[11px] text-[rgba(231,246,244,0.4)] mt-1 font-mono uppercase">
            INSPECTOR — click a node
          </div>
        )}
      </div>
      <div className="panel">
        <h3>System</h3>
        <div>
          <div className="sys-metric">
            <div className="sys-row">
              <span className="lbl">CPU</span>
              <span className={cn("pct", cpuUsage > 80 && "warn")}>{cpuUsage}%</span>
            </div>
            <div className="sys-bar">
              <div
                className="sys-bar-fill"
                style={{
                  width: `${cpuUsage}%`,
                  background: cpuUsage > 80 ? "var(--color-amber)" : "var(--color-cyan)",
                }}
              ></div>
            </div>
            <div className="sys-detail">{cpuCores} cores · {cpuName}</div>
          </div>
          
          <div className="sys-metric">
            <div className="sys-row">
              <span className="lbl">RAM</span>
              <span className={cn("pct", ramPct > 80 && "warn")}>{ramPct}%</span>
            </div>
            <div className="sys-bar">
              <div
                className="sys-bar-fill"
                style={{
                  width: `${ramPct}%`,
                  background: ramPct > 80 ? "var(--color-amber)" : "var(--color-cyan)",
                }}
              ></div>
            </div>
            <div className="sys-detail">{ramUsed} / {ramTotal} GB</div>
          </div>
          
          {gpus.map((gpu, idx) => (
            <div className="sys-metric" key={`gpu-${idx}`}>
              <div className="sys-row">
                <span className="lbl">{gpu.type === "discrete" ? "dGPU" : "iGPU"}</span>
              </div>
              <div className="sys-detail">{gpu.name}</div>
            </div>
          ))}
          
          <div className="sys-metric mt-4">
            <div className="sys-row">
              <span className="lbl">DISK (C:)</span>
              <span className={cn("pct", diskPct > 90 && "warn")}>{diskPct}%</span>
            </div>
            <div className="sys-bar">
              <div
                className="sys-bar-fill"
                style={{
                  width: `${diskPct}%`,
                  background: diskPct > 90 ? "var(--color-amber)" : "var(--color-cyan)",
                }}
              ></div>
            </div>
            <div className="sys-detail">{diskUsed} / {diskTotal} GB</div>
          </div>
          
          <div className="sys-metric mt-4">
            <div className="sys-row">
              <span className="lbl">BATTERY</span>
              <span className={cn("pct", batteryLevel < 20 && "warn")}>{batteryLevel}%</span>
            </div>
            <div className="sys-bar">
              <div
                className="sys-bar-fill"
                style={{
                  width: `${batteryLevel}%`,
                  background: batteryLevel < 20 ? "var(--color-amber)" : "#52d68a",
                }}
              ></div>
            </div>
            <div className="sys-detail">{batteryStatus}</div>
          </div>
        </div>
      </div>

      </div>

      <div className="shrink-0 mt-2 mb-5">
        <button
          className={cn("w-full h-8 rounded-lg border text-[11px] font-mono tracking-widest uppercase transition-colors flex items-center justify-center gap-2 shadow-[0_4px_12px_rgba(0,0,0,0.2)]", 
            chatMode 
              ? "bg-[rgba(82,236,227,0.15)] border-[rgba(82,236,227,0.3)] text-[var(--cyan)]" 
              : "bg-[var(--color-panel-solid)] border-[var(--color-line)] text-[var(--color-muted)] hover:border-[var(--color-line-strong)] hover:text-white"
          )}
          onClick={() => setChatMode(!chatMode)}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="w-3.5 h-3.5">
            <path d="M4 5h16v11H8l-4 4V5Z" />
            <path d="M8 9h8M8 12h5" />
          </svg>
          Chat Mode
        </button>
      </div>
    </div>
  );
}
