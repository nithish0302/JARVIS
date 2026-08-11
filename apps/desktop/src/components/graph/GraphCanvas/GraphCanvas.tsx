import { useEffect, useRef, useState } from "react";
import "./GraphCanvas.css";
import { cn } from "../../../lib/cn";
import { useAppStore } from "../../../stores/useAppStore";

const LEAVES_DATA: Record<string, string[]> = {
  skills: ["Python", "React", "TypeScript", "Rust", "FastAPI", "Tauri"],
  tools: ["Web Search", "Memory", "File System", "Terminal", "Browser", "Calculator"],
  files: ["Documents", "Downloads", "Projects", "Desktop", "Pictures", "Music"],
  notes: ["JARVIS Notes", "Ideas", "Tasks", "Meeting Notes", "Code Snippets"],
  models: ["llama3.2:3b", "qwen2.5-coder:3b", "nomic-embed-text", "OpenRouter"],
  worlds: ["Home", "Work", "Projects", "Archive"],
  conversations: []
};

const HUBS = [
  { key: "skills", label: "Skills", color: "#5aa9e6", leaves: LEAVES_DATA.skills.length },
  { key: "tools", label: "Tools", color: "#e85aa0", leaves: LEAVES_DATA.tools.length },
  { key: "files", label: "Files", color: "#7a8c93", leaves: LEAVES_DATA.files.length },
  { key: "notes", label: "Notes", color: "#52d68a", leaves: LEAVES_DATA.notes.length },
  { key: "worlds", label: "Worlds", color: "#e8934b", leaves: LEAVES_DATA.worlds.length },
  { key: "models", label: "Models", color: "#b98be8", leaves: LEAVES_DATA.models.length },
  { key: "conversations", label: "Conversations", color: "#ffb454", leaves: 0, special: true },
];

function hexToRgb(hex: string) {
  const v = parseInt(hex.slice(1), 16);
  return `${(v >> 16) & 255},${(v >> 8) & 255},${v & 255}`;
}

export function GraphCanvas() {
  const {
    graphOpen,
    setGraphOpen,
    graphFocused,
    setGraphFocused,
    setActiveHub,
    setConversationPanelOpen,
  } = useAppStore();

  const [showCaption, setShowCaption] = useState(true);

  useEffect(() => {
    if (graphOpen) {
      setShowCaption(true);
      const timer = setTimeout(() => setShowCaption(false), 3000);
      return () => clearTimeout(timer);
    } else {
      setShowCaption(true);
    }
  }, [graphOpen]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef({
    angleBase: 0,
    expandT: 1, // FIX 1: Keep initial state as Level 1 (spread)
    drillT: 0,
    selectedHub: null as any,
    mouseX: -1000,
    mouseY: -1000,
  });

  const hubNodesRef = useRef<any[]>([]);

  useEffect(() => {
    // Initialize nodes
    hubNodesRef.current = HUBS.map((h, i) => ({
      ...h,
      id: "hub-" + h.key,
      angle: (i / HUBS.length) * Math.PI * 2,
      x: 0,
      y: 0,
      isHub: true,
      leavesList: [] as any[],
    }));

    hubNodesRef.current.forEach((h) => {
      const names = LEAVES_DATA[h.key] || [];
      const numLeaves = h.leaves;
      for (let i = 0; i < numLeaves; i++) {
        const angle = (Math.PI * 2 / numLeaves) * i;
        h.leavesList.push({
          id: h.key + "-leaf-" + i,
          label: names[i] || `${h.label} ${i + 1}`,
          color: h.color,
          angle: angle,
          dist: 45 + Math.random() * 35,
          x: 0,
          y: 0,
          vx: 0,
          vy: 0,
        });
      }
    });
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const sizeCanvas = () => {
      if (!wrapRef.current) return;
      const rect = wrapRef.current.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      canvas.style.width = rect.width + "px";
      canvas.style.height = rect.height + "px";
      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    };

    window.addEventListener("resize", sizeCanvas);
    sizeCanvas();

    let animationId: number;

    const draw = () => {
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 600;
      const cx = w / 2;
      const cy = h / 2;
      ctx.clearRect(0, 0, w, h);

      const { expandT, drillT, selectedHub } = stateRef.current;
      const hubNodes = hubNodesRef.current;

      ctx.globalAlpha = 1 - drillT;
      if (ctx.globalAlpha > 0.01) {
        // Core anchor
        ctx.beginPath();
        ctx.arc(cx, cy, 14, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(82,236,227,0.28)";
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx, cy, 9, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(82,236,227,0.95)";
        ctx.shadowColor = "#52ece3";
        ctx.shadowBlur = 14;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.globalAlpha = 1;

      hubNodes.forEach((hub) => {
        const isSelected = selectedHub === hub;
        const dim = selectedHub && !isSelected;
        const linkAlpha = Math.max(0, 1 - (dim ? drillT : 0));
        
        ctx.globalAlpha = linkAlpha;
        if (linkAlpha > 0.01) {
          ctx.strokeStyle =
            hub.key === "conversations"
              ? `rgba(255,180,84,${0.25 + expandT * 0.25})`
              : `rgba(82,236,227,${0.1 + expandT * 0.22})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(hub.x, hub.y);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      });

      if (expandT > 0.04) {
        hubNodes.forEach((hub) =>
          hub.leavesList.forEach((leaf: any) => {
            const isSelectedHub = selectedHub === hub;
            const dim = selectedHub && !isSelectedHub;
            const alpha = Math.max(0, expandT - (dim ? drillT : 0));
            
            ctx.globalAlpha = alpha;
            if (alpha > 0.01) {
              ctx.strokeStyle = `rgba(${hexToRgb(hub.color)},${0.22})`;
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(hub.x, hub.y);
              ctx.lineTo(leaf.x, leaf.y);
              ctx.stroke();
            }
            ctx.globalAlpha = 1;
          })
        );
        hubNodes.forEach((hub) =>
          hub.leavesList.forEach((leaf: any) => {
            const isSelectedHub = selectedHub === hub;
            const dim = selectedHub && !isSelectedHub;
            const alpha = Math.max(0, expandT - (dim ? drillT : 0));
            
            ctx.globalAlpha = alpha;
            if (alpha > 0.01) {
              ctx.beginPath();
              ctx.arc(leaf.x, leaf.y, 5, 0, Math.PI * 2);
              ctx.fillStyle = leaf.color;
              ctx.globalAlpha = alpha * 0.8; // slightly dimmer
              ctx.shadowColor = leaf.color;
              ctx.shadowBlur = 5;
              ctx.fill();
              ctx.shadowBlur = 0;
              ctx.globalAlpha = alpha;
              
              if (isSelectedHub && drillT > 0.5) {
                ctx.font = "9px JetBrains Mono, monospace";
                ctx.fillStyle = "rgba(231,246,244,0.6)";
                ctx.textAlign = "center";
                ctx.fillText(leaf.label, leaf.x, leaf.y + 15);
                ctx.textAlign = "start";
              }
            }
            ctx.globalAlpha = 1;
          })
        );
      }

      hubNodes.forEach((hub) => {
        const isSelected = selectedHub === hub;
        const dim = selectedHub && !isSelected;
        const alpha = Math.max(0, 1 - (dim ? drillT * 0.8 : 0));
        
        ctx.globalAlpha = alpha;
        if (alpha < 0.01) {
          ctx.globalAlpha = 1;
          return;
        }
        const isConvo = hub.key === "conversations";
        const baseR = isConvo ? 9 : 8;
        hub.pulse = Math.max(0, (hub.pulse || 0) - 0.02);
        const pulseR = baseR + (hub.pulse || 0) * 10;
        if (isConvo && hub.pulse > 0) {
          ctx.beginPath();
          ctx.arc(hub.x, hub.y, pulseR, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(255,180,84,${hub.pulse * 0.6})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
        ctx.globalAlpha = dim ? 0.3 : 1;
        ctx.beginPath();
        ctx.arc(hub.x, hub.y, baseR, 0, Math.PI * 2);
        ctx.fillStyle = hub.color;
        ctx.shadowColor = hub.color;
        ctx.shadowBlur = isConvo ? 16 : 10;
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
        if (isConvo) {
          ctx.font = "14px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "#1a0f00";
          ctx.fillText("\uD83D\uDCAC", hub.x, hub.y + 0.5);
          ctx.textAlign = "start";
          ctx.textBaseline = "alphabetic";
        }
        
        ctx.globalAlpha = expandT; // hide in Level 0
        if (expandT > 0.05) {
            ctx.font = "600 11px Rajdhani, sans-serif";
            ctx.fillStyle = isConvo ? "rgba(255,180,84,0.9)" : "rgba(231,246,244,0.75)";
            ctx.fillText(hub.label, hub.x + 14, hub.y + 4);
        }
        
        ctx.globalAlpha = 1;
      });
      
      if (drillT > 0.05) {
        ctx.globalAlpha = drillT;
        ctx.font = "600 13px JetBrains Mono, monospace";
        ctx.fillStyle = "rgba(82,236,227,0.7)";
        ctx.fillText("← BACK", 20, 30);
        ctx.globalAlpha = 1;
      }
    };

    const layout = (speedMultiplier: number) => {
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 600;
      const cx = w / 2;
      const cy = h / 2;
      const canvasRadius = Math.min(w, h) * 0.5;
      const LEVEL_0_RADIUS = canvasRadius * 0.12;
      const LEVEL_1_RADIUS = canvasRadius * 0.32;
      
      const { expandT, drillT, selectedHub } = stateRef.current;
      const r = LEVEL_0_RADIUS + (LEVEL_1_RADIUS - LEVEL_0_RADIUS) * expandT;

      hubNodesRef.current.forEach((hub) => {
        const a = hub.angle + stateRef.current.angleBase * (hub.key === "conversations" ? 0.6 : 1);
        
        let targetHubX = cx + Math.cos(a) * r;
        let targetHubY = cy + Math.sin(a) * r;
        
        if (selectedHub) {
            if (selectedHub === hub) {
                targetHubX = targetHubX + (cx - targetHubX) * drillT;
                targetHubY = targetHubY + (cy - targetHubY) * drillT;
            } else {
                targetHubX = targetHubX + (targetHubX - cx) * 0.5 * drillT;
                targetHubY = targetHubY + (targetHubY - cy) * 0.5 * drillT;
            }
        }
        
        hub.x = targetHubX;
        hub.y = targetHubY;
        
        const LEAF_ORBIT_RADIUS = canvasRadius * 0.56;
        const LEAF_ORBIT_SPEED = 0.003 * speedMultiplier;

        hub.leavesList.forEach((leaf: any) => {
          if (selectedHub === hub) {
            leaf.angle += LEAF_ORBIT_SPEED;
            const targetDist = LEAF_ORBIT_RADIUS;
            const startDist = leaf.dist * (0.2 + expandT * 0.2); // tighter in level 0
            const currentDist = startDist + (targetDist - startDist) * drillT;
            leaf.x = hub.x + Math.cos(leaf.angle) * currentDist;
            leaf.y = hub.y + Math.sin(leaf.angle) * currentDist;
          } else {
            const leafExpand = 0.2 + expandT * 0.2; // tight cluster around hub in level 0
            leaf.x = hub.x + Math.cos(leaf.angle) * leaf.dist * leafExpand;
            leaf.y = hub.y + Math.sin(leaf.angle) * leaf.dist * leafExpand;
          }
        });
      });
    };

    const loop = () => {
      const HOVER_RADIUS = 60;
      const NORMAL_SPEED = 1.0;
      const HOVER_SPEED = 0.15;
      let speedMultiplier = NORMAL_SPEED;

      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 600;
      const cx = w / 2;
      const cy = h / 2;
      const mx = stateRef.current.mouseX;
      const my = stateRef.current.mouseY;

      let isHovering = false;
      if (Math.hypot(mx - cx, my - cy) < HOVER_RADIUS) {
        speedMultiplier = HOVER_SPEED;
        isHovering = true;
      }
      
      hubNodesRef.current.forEach(hub => {
        if (Math.hypot(mx - hub.x, my - hub.y) < HOVER_RADIUS) {
          speedMultiplier = HOVER_SPEED;
          isHovering = true;
        }
      });
      
      canvas.style.cursor = isHovering ? "pointer" : "default";

      stateRef.current.angleBase += 0.0018 * speedMultiplier;
      const targetExpand = graphOpen ? 1 : 0;
      const targetDrill = stateRef.current.selectedHub ? 1 : 0;
      
      stateRef.current.expandT += (targetExpand - stateRef.current.expandT) * 0.05;
      stateRef.current.drillT += (targetDrill - stateRef.current.drillT) * 0.08;
      
      layout(speedMultiplier);
      draw();
      animationId = requestAnimationFrame(loop);
    };

    animationId = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener("resize", sizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, [graphOpen]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const w = canvas.clientWidth || 800;
    const h = canvas.clientHeight || 600;
    const cx = w / 2;
    const cy = h / 2;

    if (stateRef.current.selectedHub) {
      if (mx > 10 && mx < 80 && my > 10 && my < 40) {
        stateRef.current.selectedHub = null;
        setActiveHub(null);
        return;
      }
      
      if (Math.hypot(mx - cx, my - cy) < 20) {
        stateRef.current.selectedHub = null;
        setActiveHub(null);
        return;
      }
    } else {
      if (Math.hypot(mx - cx, my - cy) < 15) {
        setGraphOpen(!graphOpen);
        setGraphFocused(true);
        stateRef.current.selectedHub = null;
        setActiveHub(null);
        return;
      }
    }

    let hit: any = null;
    let best = 20;
    hubNodesRef.current.forEach((hub) => {
      if (stateRef.current.selectedHub && stateRef.current.selectedHub !== hub) return;
      
      const d = Math.hypot(hub.x - mx, hub.y - my);
      if (d < best) {
        hit = hub;
        best = d;
      }
    });

    if (hit && hit.key === "conversations") {
      stateRef.current.selectedHub = null;
      setActiveHub("conversations");
      setConversationPanelOpen(true);
      return;
    }

    if (hit) {
      if (!graphOpen) setGraphOpen(true);
      setGraphFocused(true);
      stateRef.current.selectedHub = hit;
      setActiveHub(hit.key || hit.id);
    } else {
      if (!stateRef.current.selectedHub) {
          stateRef.current.selectedHub = null;
          setActiveHub(null);
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    stateRef.current.mouseX = e.clientX - rect.left;
    stateRef.current.mouseY = e.clientY - rect.top;
  };

  return (
    <div className={cn("canvas-wrap", !graphFocused && "chat-focused")} ref={wrapRef}>
      <canvas id="graphCanvas" ref={canvasRef} onClick={handleCanvasClick} onMouseMove={handleMouseMove}></canvas>
      <div className={cn("graph-caption transition-opacity duration-1000", (!showCaption || (graphOpen && stateRef.current.selectedHub)) && "opacity-0")}>
        {graphOpen
          ? 'graph navigation active — press ← BACK to zoom out'
          : 'say "jarvis" — ask to see your brain'}
      </div>
    </div>
  );
}
