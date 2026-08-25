import { useEffect, useState } from "react";
import "../../../styles/Panels.css";
import "./LeftColumn.css";
import { useAppStore } from "../../../stores/useAppStore";
import { useAIStore } from "../../../stores/useAIStore";
import { useMicLevelStore } from "../../../stores/useMicLevelStore";
import { cn } from "../../../lib/cn";
import { invoke } from "@tauri-apps/api/core";
import { MemoryInspector } from "./MemoryInspector";

// Mic RMS levels from the backend run well under 1.0 for normal room tone
// and speech (silence_threshold=0.01, TTS_INTERRUPT_LEVEL_THRESHOLD=0.18 -
// see core/config.py / speech_recorder.py), so rendering the raw value
// directly as a 0-1 scale factor collapses every bar toward zero height -
// it "reacts" per-sample but the variation is imperceptible, reading as a
// flat line. Apply the same kind of gain the old dock meter used
// (0.35 + level * 1.4) so realistic levels actually fill the visible range.
const WAVEFORM_GAIN = 5;
function ampLevel(raw: number): number {
  return Math.min(1, Math.max(0, raw) * WAVEFORM_GAIN);
}

// Render fewer, denser bars than the store's raw 40-sample history buffer -
// 40 individual hairline bars read as visual noise. Averaging consecutive
// samples into groups keeps the underlying data (and responsiveness)
// untouched while thinning the display down to a clean bar count.
const WAVEFORM_BAR_COUNT = 20;
function averageGroups(values: number[], groupCount: number): number[] {
  if (values.length === 0) return Array(groupCount).fill(0);
  const result: number[] = [];
  for (let i = 0; i < groupCount; i++) {
    const start = Math.floor((i * values.length) / groupCount);
    const end = Math.max(start + 1, Math.floor(((i + 1) * values.length) / groupCount));
    const slice = values.slice(start, end);
    result.push(slice.reduce((a, b) => a + b, 0) / slice.length);
  }
  return result;
}

export function LeftColumn() {
  const graphOpen = useAppStore(state => state.graphOpen);
  const activeHub = useAppStore(state => state.activeHub);
  const chatMode = useAppStore(state => state.chatMode);
  const setChatMode = useAppStore(state => state.setChatMode);
  const inspectorMessage = useAppStore(state => state.inspectorMessage);
  const micLevel = useMicLevelStore(state => state.level);
  const micHistory = useMicLevelStore(state => state.history);
  const waveformBars = averageGroups(micHistory, WAVEFORM_BAR_COUNT);
  const voiceStatus = useAIStore(state => state.voiceStatus);
  const isContinuousMode = voiceStatus === "continuous";

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
    if (activeHub === "memories") {
      return <MemoryInspector />;
    }
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
      <div className="panel mic-waveform-panel" id="mic-waveform">
        <h3 className="flex items-center justify-between">
          Audio Input
          <span className="text-[10px] text-[var(--color-cyan)] opacity-70">LIVE</span>
        </h3>
        {/* Status indicator, not a control: listening cannot be turned off
            from here (or anywhere) - wake-word detection is started
            unconditionally by the backend's lifespan (voice_manager.initialize).
            The bars are driven by the store's rolling history buffer, so this
            reads as an actual waveform rather than a single-value meter. */}
        <div
          className="mic-waveform"
          role="img"
          aria-label="Live microphone input waveform, showing ambient and voice level"
          title={
            isContinuousMode
              ? 'Continuous conversation mode — say a command, or "go to sleep" to end it.'
              : 'Microphone is live — listening for "wake up jarvis". Bars react to the current mic level.'
          }
        >
          <span
            className="mic-waveform-glow"
            style={{
              opacity: 0.2 + ampLevel(micLevel) * 0.5,
              transform: `scale(${1 + ampLevel(micLevel) * 0.06})`,
            }}
          />
          <div className="mic-waveform-bars">
            {waveformBars.map((v, i) => (
              <span key={i} style={{ transform: `scaleY(${Math.max(0.05, ampLevel(v))})` }} />
            ))}
          </div>
        </div>
        <div className="mic-waveform-caption">
          {isContinuousMode
            ? 'Continuous mode — say a command or "go to sleep"'
            : 'Listening for "wake up jarvis"'}
        </div>
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
                <span className="pct">{gpu.static ? "—" : `${gpu.usage ?? 0}%`}</span>
              </div>
              {!gpu.static && (
                <div className="sys-bar">
                  <div
                    className="sys-bar-fill"
                    style={{
                      width: `${gpu.usage ?? 0}%`,
                      background: (gpu.usage ?? 0) > 80 ? "var(--color-amber)" : "var(--color-cyan)",
                    }}
                  ></div>
                </div>
              )}
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
