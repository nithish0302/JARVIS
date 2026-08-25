import { useEffect, useRef } from "react";
import "./Orb.css";
import { cn } from "../../../lib/cn";
import { useAIStore, type AIState } from "../../../stores/useAIStore";
import { useAppStore } from "../../../stores/useAppStore";
import { ActionFeedback } from "../ActionFeedback/ActionFeedback";

type EffectiveStatus = "idle" | "listening" | "speaking" | "thinking" | "error";

function getEffectiveStatus(status: AIState["status"], voiceStatus: AIState["voiceStatus"]): EffectiveStatus {
  // Combine status - voice takes priority
  return voiceStatus === "listening" ? "listening" :
    voiceStatus === "speaking" ? "speaking" :
    voiceStatus === "processing" ? "thinking" :
    status === "streaming" ? "thinking" :
    status === "connecting" ? "thinking" :
    status === "error" ? "error" :
    "idle";
}

function getOrbCaption(effectiveStatus: EffectiveStatus): string {
  if (effectiveStatus === "listening") return "listening...";
  if (effectiveStatus === "speaking") return "speaking...";
  if (effectiveStatus === "thinking") return "processing...";
  if (effectiveStatus === "error") return "check connection";
  return 'say "wake up jarvis"...';
}

// Primary status readout: caption + provider/model, rendered prominently
// above the graph canvas (GraphCanvas) and at the top of Chat Mode
// (ChatFullView) - same component, same look, in both places. Reads the
// same AI status as Orb but independently, since it no longer lives inside
// Orb (or the sidebar at all).
export function OrbCaption() {
  const { status, voiceStatus, provider, model } = useAIStore();
  const effectiveStatus = getEffectiveStatus(status, voiceStatus);

  return (
    <div className="orb-caption-readout">
      <div className="orb-caption">{getOrbCaption(effectiveStatus)}</div>
      <div className="orb-sub">
        {model} · {provider}
      </div>
    </div>
  );
}

export function Orb() {
  const { status, voiceStatus } = useAIStore();
  const { graphMode } = useAppStore();

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const statusRef = useRef(status);
  const voiceStatusRef = useRef(voiceStatus);
  const graphModeRef = useRef(graphMode);

  const effectiveStatus = getEffectiveStatus(status, voiceStatus);

  const effectiveStatusRef = useRef(effectiveStatus);

  // Update status refs
  useEffect(() => {
    statusRef.current = status;
    voiceStatusRef.current = voiceStatus;
    effectiveStatusRef.current = effectiveStatus;
  }, [status, voiceStatus, effectiveStatus]);

  // Update graphMode ref
  useEffect(() => {
    graphModeRef.current = graphMode;
  }, [graphMode]);

  useEffect(() => {
    const canvasEl = canvasRef.current;
    if (!canvasEl) return;
    const canvas: HTMLCanvasElement = canvasEl;

    const ctx = canvas.getContext("2d")!;
    const wrapper = canvas.parentElement!;

    const DPR = window.devicePixelRatio || 1;
    const TAU = Math.PI * 2;
    const DEG = Math.PI / 180;

    // Canvas geometry tracks the actual rendered size of orb-canvas-wrapper
    // (which is clamp()-based on viewport height) rather than a fixed constant.
    let SIZE = 200;
    let cx = 100;
    let cy = 100;
    let R = 76;

    function resize() {
      const rect = wrapper.getBoundingClientRect();
      const size = Math.max(1, Math.round(Math.min(rect.width, rect.height))) || 200;
      SIZE = size;
      cx = SIZE / 2;
      cy = SIZE / 2;
      R = SIZE * 0.38;
      canvas.width = SIZE * DPR;
      canvas.height = SIZE * DPR;
      canvas.style.width = SIZE + "px";
      canvas.style.height = SIZE + "px";
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    }
    resize();

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(wrapper);

    // Drawing primitives
    function arc(cx: number, cy: number, r: number, s: number, e: number, w: number, c: string, a = 1) {
      ctx.save();
      ctx.globalAlpha = a;
      ctx.beginPath();
      ctx.arc(cx, cy, r, s * DEG, e * DEG);
      ctx.strokeStyle = c;
      ctx.lineWidth = w;
      ctx.lineCap = "butt";
      ctx.stroke();
      ctx.restore();
    }

    function arcGlow(cx: number, cy: number, r: number, s: number, e: number, w: number, c: string, g = 14, a = 1) {
      ctx.save();
      ctx.globalAlpha = a;
      ctx.beginPath();
      ctx.arc(cx, cy, r, s * DEG, e * DEG);
      ctx.strokeStyle = c;
      ctx.lineWidth = w;
      ctx.lineCap = "round";
      ctx.shadowColor = c;
      ctx.shadowBlur = g;
      ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.restore();
    }

    function ticks(cx: number, cy: number, ri: number, ro: number, n: number, off: number, w: number, c: string, a = 1) {
      ctx.save();
      ctx.globalAlpha = a;
      ctx.strokeStyle = c;
      ctx.lineWidth = w;
      ctx.lineCap = "butt";
      for (let i = 0; i < n; i++) {
        const ang = (i / n) * TAU + off * DEG;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(ang) * ri, cy + Math.sin(ang) * ri);
        ctx.lineTo(cx + Math.cos(ang) * ro, cy + Math.sin(ang) * ro);
        ctx.stroke();
      }
      ctx.restore();
    }

    function dot(x: number, y: number, r: number, c: string, g = 10) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, TAU);
      ctx.fillStyle = c;
      ctx.shadowColor = c;
      ctx.shadowBlur = g;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.restore();
    }

    function sweep(cx: number, cy: number, r: number, startDeg: number, lenDeg: number, w: number, c: string, a = 1) {
      ctx.save();
      ctx.globalAlpha = a;
      for (let i = 0; i < lenDeg; i += 1) {
        const frac = i / lenDeg;
        const alpha = frac * frac;
        const a1 = (startDeg + i) * DEG;
        const a2 = (startDeg + i + 1.5) * DEG;
        ctx.globalAlpha = a * alpha;
        ctx.beginPath();
        ctx.arc(cx, cy, r, a1, a2);
        ctx.strokeStyle = c;
        ctx.lineWidth = w;
        ctx.lineCap = "butt";
        ctx.shadowColor = c;
        ctx.shadowBlur = alpha * 16;
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
      ctx.restore();
    }

    function bracket(cx: number, cy: number, r: number, angleDeg: number, size: number, w: number, c: string, a = 1, flip = false) {
      ctx.save();
      ctx.globalAlpha = a;
      const ang = angleDeg * DEG;
      const cos = Math.cos(ang);
      const sin = Math.sin(ang);
      const px = cx + cos * r;
      const py = cy + sin * r;
      const nx = -sin;
      const ny = cos;
      const dir = flip ? -1 : 1;
      ctx.beginPath();
      ctx.moveTo(px + nx * size * dir, py + ny * size * dir);
      ctx.lineTo(px, py);
      ctx.lineTo(px + cos * size, py + sin * size);
      ctx.strokeStyle = c;
      ctx.lineWidth = w;
      ctx.lineCap = "butt";
      ctx.stroke();
      ctx.restore();
    }

    const getSpeed = () => {
      switch (effectiveStatusRef.current) {
        case "listening":
          return 2.5;  // Fast pulse for listening
        case "speaking":
          return 1.8;  // Medium-fast for speaking
        case "thinking":
          return 2.0;  // Fast spin for thinking
        case "error":
          return 0.3;  // Slow for error
        default:
          return 1.0;  // Normal for idle
      }
    };

    const startTime = performance.now();
    let animId: number;
    let lastStatus = statusRef.current;
    let lastMode = graphModeRef.current;
    let hasDrawn2D = false;

    function draw() {
      // Pause animation when app is hidden/minimized
      if (document.hidden) {
        animId = window.setTimeout(draw, 1000) as unknown as number;
        return;
      }

      const currentMode = graphModeRef.current;
      const currentStatus = statusRef.current;

      // GPU OPTIMIZATION: In 2D mode, draw once then stop
      if (currentMode === "2d" && hasDrawn2D &&
          currentStatus === lastStatus && lastMode === "2d") {
        // Already drawn and nothing changed - skip redraw
        animId = window.setTimeout(draw, 1000) as unknown as number;
        return;
      }

      ctx.clearRect(0, 0, SIZE, SIZE);

      const elapsed = (performance.now() - startTime) / 1000;
      const isAnimating = currentMode === "3d";
      const time = isAnimating
        ? elapsed * 0.6 * getSpeed()
        : 0;  // frozen at time=0 when 2D
      const cyan = "rgba(100,210,255,";
      const amber = "rgba(255,193,7,";

      // LAYER 1 — OUTERMOST CLEAN RING
      const r1 = R * 1.02;
      const rot1 = time * 10;
      arc(cx, cy, r1, 0, 360, 2, cyan + "0.4)", 1);
      sweep(cx, cy, r1, rot1 * 3, 100, 3, cyan + "1)", 0.75);
      arc(cx, cy, r1 + 16, 0, 360, 0.5, cyan + "0.06)", 1);

      // LAYER 2 — THICK BRIGHT CYAN BAND (FIXED)
      const r2 = R * 0.92;
      arc(cx, cy, r2, 0, 360, 6, cyan + "0.18)", 1);
      arcGlow(cx, cy, r2, 0, 85, 6, cyan + "0.6)", 20, 0.9);
      arcGlow(cx, cy, r2, 120, 210, 6, cyan + "0.45)", 16, 0.7);
      arcGlow(cx, cy, r2, 250, 320, 5, cyan + "0.4)", 14, 0.6);
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * 360;
        arc(cx, cy, r2, a, a + 4, 9, cyan + "0.55)", 0.7);
      }
      [45, 135, 225, 315].forEach((d, i) => {
        bracket(cx, cy, r2 + 4, d, 6, 1.5, cyan + "0.45)", 0.6, i % 2 === 0);
      });

      // LAYER 3 — THIN SEPARATOR RING
      const r3 = R * 0.84;
      arc(cx, cy, r3, 0, 360, 1, cyan + "0.2)", 1);
      ctx.save();
      ctx.setLineDash([3, 9]);
      arc(cx, cy, r3, 0, 360, 0.8, cyan + "0.12)", 1);
      ctx.setLineDash([]);
      ctx.restore();

      // LAYER 4 — DENSE GAUGE TICK RING
      const r4 = R * 0.78;
      const rot4 = time * 4;
      arc(cx, cy, r4, 0, 360, 1.2, cyan + "0.15)", 1);
      ticks(cx, cy, r4 - 10, r4, 100, rot4, 1.0, cyan + "0.3)", 1);
      ticks(cx, cy, r4 - 5, r4, 250, rot4, 0.4, cyan + "0.12)", 1);
      const hlStart = rot4 * 2;
      for (let i = 0; i < 25; i++) {
        const a = (hlStart + i * 1.4) * DEG;
        ctx.save();
        ctx.globalAlpha = 0.5;
        ctx.strokeStyle = cyan + "0.7)";
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a) * (r4 - 10), cy + Math.sin(a) * (r4 - 10));
        ctx.lineTo(cx + Math.cos(a) * r4, cy + Math.sin(a) * r4);
        ctx.stroke();
        ctx.restore();
      }

      // AMBER ACCENT ARC
      const rAmber = R * 0.85;
      const amberCenter = time * 25;
      const amberHalf = 32;
      arcGlow(cx, cy, rAmber, amberCenter - amberHalf, amberCenter + amberHalf, 7, amber + "0.9)", 22, 0.95);
      arcGlow(cx, cy, rAmber - 8, amberCenter - amberHalf + 8, amberCenter + amberHalf - 8, 3, amber + "0.45)", 10, 0.55);
      arcGlow(cx, cy, rAmber + 5, amberCenter - amberHalf + 3, amberCenter + amberHalf - 3, 1.5, amber + "0.2)", 8, 0.3);
      [amberCenter - 20, amberCenter, amberCenter + 20].forEach((deg) => {
        const a = deg * DEG;
        const x = cx + Math.cos(a) * (rAmber + 12);
        const y = cy + Math.sin(a) * (rAmber + 12);
        dot(x, y, 3, `rgba(255,220,50,0.85)`, 12);
      });

      // LAYER 5 — INNER THICK SEGMENTED RING
      const r5 = R * 0.65;
      const rot5 = -time * 12;
      arc(cx, cy, r5, 0, 360, 1, cyan + "0.08)", 1);
      const segCount = 16;
      const segGap = 4;
      const segArc = 360 / segCount - segGap;
      for (let i = 0; i < segCount; i++) {
        const start = (i / segCount) * 360 + rot5;
        const bright = i % 4 === 0 ? 0.45 : i % 2 === 0 ? 0.25 : 0.15;
        arc(cx, cy, r5, start, start + segArc, 10, cyan + bright + ")", 1);
      }
      const segHL = (time * 25) % 360;
      arcGlow(cx, cy, r5, segHL + rot5, segHL + rot5 + 45, 10, cyan + "0.55)", 12, 0.7);
      arcGlow(cx, cy, r5, segHL + rot5 + 180, segHL + rot5 + 210, 10, cyan + "0.3)", 8, 0.4);

      // LAYER 6 — THIN INNER RING + TICKS
      const r6 = R * 0.54;
      const rot6 = time * 3;
      arc(cx, cy, r6, 0, 360, 1, cyan + "0.15)", 1);
      ticks(cx, cy, r6, r6 + 6, 30, rot6, 0.8, cyan + "0.25)", 1);
      sweep(cx, cy, r6, -time * 18, 70, 1.8, cyan + "0.8)", 0.5);

      // LAYER 7 — INNERMOST DECORATIVE RING
      const r7 = R * 0.47;
      arc(cx, cy, r7, 0, 360, 0.8, cyan + "0.1)", 1);
      ctx.save();
      ctx.setLineDash([2, 6]);
      arc(cx, cy, r7, 0, 360, 0.7, cyan + "0.12)", 1);
      ctx.setLineDash([]);
      ctx.restore();
      arcGlow(cx, cy, r7, 30, 90, 1.5, cyan + "0.3)", 6, 0.4);
      arcGlow(cx, cy, r7, 210, 260, 1.5, cyan + "0.25)", 6, 0.35);

      // CENTER DISC
      const rC = R * 0.44;
      ctx.save();
      const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, rC);
      cg.addColorStop(0, "rgba(6,16,32,0.96)");
      cg.addColorStop(0.7, "rgba(4,12,26,0.93)");
      cg.addColorStop(1, "rgba(3,10,22,0.88)");
      ctx.beginPath();
      ctx.arc(cx, cy, rC, 0, TAU);
      ctx.fillStyle = cg;
      ctx.fill();
      ctx.restore();

      // Circuit grid pattern
      ctx.save();
      const gridAlpha = 0.07 + Math.sin(time * 0.5) * 0.02;
      ctx.globalAlpha = gridAlpha;
      ctx.strokeStyle = cyan + "1)";
      ctx.lineWidth = 0.5;
      const gridStep = rC / 7;
      for (let i = -6; i <= 6; i++) {
        const y = cy + i * gridStep;
        const dx = Math.sqrt(Math.max(0, rC * rC - (i * gridStep) ** 2));
        if (dx < 4) continue;
        ctx.beginPath();
        ctx.moveTo(cx - dx * 0.88, y);
        ctx.lineTo(cx + dx * 0.88, y);
        ctx.stroke();
      }
      for (let i = -6; i <= 6; i++) {
        const x = cx + i * gridStep;
        const dy = Math.sqrt(Math.max(0, rC * rC - (i * gridStep) ** 2));
        if (dy < 4) continue;
        ctx.beginPath();
        ctx.moveTo(x, cy - dy * 0.88);
        ctx.lineTo(x, cy + dy * 0.88);
        ctx.stroke();
      }

      // Random circuit traces
      ctx.globalAlpha = 0.1 + Math.sin(time * 0.8) * 0.03;
      ctx.lineWidth = 0.8;
      const seed = Math.floor(time * 0.2) * 137;
      for (let i = 0; i < 18; i++) {
        const sx = cx + Math.cos(seed + i * 41) * rC * 0.55;
        const sy = cy + Math.sin(seed + i * 67) * rC * 0.35;
        const ex = sx + (Math.cos(seed + i * 23) > 0 ? 1 : -1) * (8 + (i % 5) * 7);
        const ey = sy;
        if (Math.hypot(sx - cx, sy - cy) > rC * 0.82) continue;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(ex, ey);
        ctx.lineTo(ex, ey + (Math.sin(seed + i * 31) > 0 ? 1 : -1) * (5 + (i % 4) * 4));
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(ex, ey, 1, 0, TAU);
        ctx.fillStyle = cyan + "0.15)";
        ctx.fill();
      }
      ctx.restore();

      // Ring glow around center disc
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, rC, 0, TAU);
      ctx.strokeStyle = cyan + "0.2)";
      ctx.lineWidth = 1.5;
      ctx.shadowColor = "rgba(79,195,247,0.35)";
      ctx.shadowBlur = 12;
      ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.restore();

      // Loading bar inside center
      const barW = rC * 1.0;
      const barH = 3;
      const barY = cy + rC * 0.78;
      const barX = cx - barW / 2;
      const progress = (time * 0.3) % 1;
      ctx.save();
      ctx.globalAlpha = 0.15;
      ctx.fillStyle = cyan + "0.3)";
      ctx.fillRect(barX, barY, barW, barH);
      ctx.globalAlpha = 0.4;
      ctx.fillStyle = cyan + "0.7)";
      ctx.fillRect(barX, barY, barW * progress, barH);
      ctx.shadowColor = "rgba(79,195,247,0.8)";
      ctx.shadowBlur = 8;
      ctx.fillRect(barX + barW * progress - 3, barY - 1, 6, barH + 2);
      ctx.shadowBlur = 0;
      ctx.restore();

      // J.A.R.V.I.S text in center
      const textScale = SIZE / 200;
      ctx.save();
      ctx.font = `bold ${18 * textScale}px 'Orbitron', monospace`;
      ctx.fillStyle = "rgba(255,255,255,0.95)";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.shadowColor = "rgba(79,195,247,0.7)";
      ctx.shadowBlur = 20;
      ctx.fillText("J.A.R.V.I.S.", cx, cy - 8);
      ctx.shadowBlur = 0;
      ctx.font = `600 ${11 * textScale}px 'Rajdhani', monospace`;
      ctx.fillStyle = "rgba(79,195,247,0.7)";
      ctx.fillText("ONLINE", cx, cy + 8);
      ctx.restore();

      // Cardinal dots on ring 2
      [0, 90, 180, 270].forEach((deg) => {
        const a = deg * DEG;
        const x = cx + Math.cos(a) * (r2 + 2);
        const y = cy + Math.sin(a) * (r2 + 2);
        dot(x, y, 2.5, `rgba(100,210,255,0.65)`, 10);
      });

      // Beacon dot
      const bAng = (-90 + rot1 * 0.7) * DEG;
      const bx = cx + Math.cos(bAng) * (r1 + 4);
      const by = cy + Math.sin(bAng) * (r1 + 4);
      dot(bx, by, 3.5, `rgba(120,230,255,0.85)`, 18);

      // Small amber accent
      const amberR2 = time * 15;
      arcGlow(cx, cy, r5 + 2, amberR2, amberR2 + 20, 2.5, amber + "0.5)", 8, 0.5);

      // Floating particles
      ctx.save();
      for (let i = 0; i < 35; i++) {
        const angle = (i / 35) * TAU + time * 0.25 + i * 0.8;
        const dist = R * (0.45 + 0.65 * ((Math.sin(time * 0.18 + i * 2.3) + 1) / 2));
        const px = cx + Math.cos(angle) * dist;
        const py = cy + Math.sin(angle) * dist;
        const pa = 0.05 + Math.sin(time * 1.3 + i * 3.1) * 0.04;
        const ps = 0.6 + Math.sin(time + i) * 0.5;
        ctx.globalAlpha = pa;
        ctx.beginPath();
        ctx.arc(px, py, ps, 0, TAU);
        ctx.fillStyle = cyan + "1)";
        ctx.fill();
      }
      ctx.restore();

      // Outer decorative arcs
      const rH = R * 1.12;
      arc(cx, cy, rH, 0, 360, 0.4, cyan + "0.04)", 1);
      arcGlow(cx, cy, rH, rot1 * 0.4 + 20, rot1 * 0.4 + 55, 1.2, cyan + "0.2)", 5, 0.3);
      arcGlow(cx, cy, rH, rot1 * 0.4 + 190, rot1 * 0.4 + 235, 1.2, cyan + "0.15)", 5, 0.25);

      // Very faint outermost whisper ring
      const rH2 = R * 1.18;
      arc(cx, cy, rH2, 0, 360, 0.3, cyan + "0.025)", 1);

      // GPU OPTIMIZATION: Adaptive frame rate
      const statusChanged = lastStatus !== currentStatus;
      const modeChanged = lastMode !== currentMode;
      lastStatus = currentStatus;
      lastMode = currentMode;

      if (currentMode === "2d") {
        hasDrawn2D = true;
      } else {
        hasDrawn2D = false;
      }

      if (currentMode === "3d" || statusChanged || modeChanged) {
        // 3D mode or status change: 60fps smooth animation
        animId = requestAnimationFrame(draw);
      } else {
        // 2D mode and stable: check once per second
        animId = window.setTimeout(draw, 1000) as unknown as number;
      }
    }

    // Start the loop
    if (graphModeRef.current === "3d") {
      animId = requestAnimationFrame(draw);
    } else {
      animId = window.setTimeout(draw, 1000) as unknown as number;
    }

    return () => {
      resizeObserver.disconnect();
      cancelAnimationFrame(animId);
      clearTimeout(animId);
    };
  }, []);

  const statusText = {
    idle: "IDLE",
    listening: "LISTENING",
    speaking: "SPEAKING",
    thinking: "THINKING...",
    error: "ERROR",
  }[effectiveStatus] || "IDLE";

  const statusColor = {
    idle: "#52ece3",      // cyan
    listening: "#22c55e", // green
    speaking: "#a78bfa",  // violet
    thinking: "#ffb454",  // amber
    error: "#ef4444",     // red
  }[effectiveStatus] || "#52ece3";

  return (
    <div className="orb-card">
      <div className="orb-canvas-wrapper">
        <canvas ref={canvasRef} style={{ display: "block" }} />
      </div>
      <div className={cn("orb-status-row", effectiveStatus !== "idle" && effectiveStatus)}>
        <span className="dot" style={{ backgroundColor: statusColor }}></span>
        <span className="orb-status" style={{ color: statusColor }}>{statusText}</span>
      </div>
      <ActionFeedback />
    </div>
  );
}
