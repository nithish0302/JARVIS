import { useEffect, useState } from "react";
import "../../../styles/Panels.css";
import { useAppStore } from "../../../stores/useAppStore";
import { cn } from "../../../lib/cn";
import { invoke } from "@tauri-apps/api/core";

export function LeftColumn() {
  const { graphOpen, activeHub } = useAppStore();

  const [cpuUsage, setCpuUsage] = useState(0);
  const [cpuName, setCpuName] = useState("Unknown CPU");
  const [cpuCores, setCpuCores] = useState(0);
  const [ramPct, setRamPct] = useState(0);
  const [ramUsed, setRamUsed] = useState("0");
  const [ramTotal, setRamTotal] = useState("0");
  const [gpus, setGpus] = useState<any[]>([]);

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

    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => {
      mounted = false;
      clearInterval(interval);
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
    <div className="side-col max-lg:hidden">
      <div className={cn("panel", activeHub ? "flex-[0_0_auto]" : "flex-[0_0_auto]")} id="inspector">
        <h3 className="flex items-center justify-between">
          Inspector
          <span className="text-[10px] text-[var(--color-cyan)] opacity-70">
            {activeHub ? "▼" : "▶"}
          </span>
        </h3>
        {activeHub ? (
          renderInspectorContent()
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
                <span className="pct">{gpu.usage}%</span>
              </div>
              <div className="sys-bar">
                <div
                  className="sys-bar-fill"
                  style={{
                    width: `${Math.max(1, gpu.usage)}%`,
                    background: gpu.name.includes("GTX") ? "#52d68a" : "#5aa9e6",
                  }}
                ></div>
              </div>
              <div className="sys-detail">{gpu.name} <span className="opacity-50">(static)</span></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
