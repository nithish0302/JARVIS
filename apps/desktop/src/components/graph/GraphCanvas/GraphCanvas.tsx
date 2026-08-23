import { useEffect, useRef, useState } from "react";
import "./GraphCanvas.css";
import { cn } from "../../../lib/cn";
import { useAppStore } from "../../../stores/useAppStore";
import { useConversationStore } from "../../../stores/useConversationStore";
import { HUB_LEAVES as LEAVES_DATA, GRAPH_HUBS as HUBS } from "../../../data/graphHubs";

function hexToRgb(hex: string) {
  const v = parseInt(hex.slice(1), 16);
  return `${(v >> 16) & 255},${(v >> 8) & 255},${v & 255}`;
}

export function GraphCanvas() {
  const graphOpen = useAppStore(state => state.graphOpen);
  const setGraphOpen = useAppStore(state => state.setGraphOpen);
  const graphFocused = useAppStore(state => state.graphFocused);
  const setGraphFocused = useAppStore(state => state.setGraphFocused);
  const activeHub = useAppStore(state => state.activeHub);
  const setActiveHub = useAppStore(state => state.setActiveHub);
  const graphLevel = useAppStore(state => state.graphLevel);
  const setGraphLevel = useAppStore(state => state.setGraphLevel);
  const graphMode = useAppStore(state => state.graphMode);

  // Use a ref so the animation loop sees graphMode updates
  const graphModeRef = useRef(graphMode);
  useEffect(() => {
    graphModeRef.current = graphMode;
  }, [graphMode]);

  const draw3DNode = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    radius: number,
    color: string
  ) => {
    // Subtle outer glow (not too large)
    const glow = ctx.createRadialGradient(
      x, y, 0, x, y, radius * 2.5
    )
    glow.addColorStop(0, color + "30")
    glow.addColorStop(1, "transparent")
    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(x, y, radius * 2.5, 0, Math.PI * 2)
    ctx.fill()

    // 3D sphere gradient
    const sphere = ctx.createRadialGradient(
      x - radius * 0.35,
      y - radius * 0.35,
      0,
      x, y,
      radius
    )
    sphere.addColorStop(0, color + "ff")
    sphere.addColorStop(0.6, color + "cc")
    sphere.addColorStop(1, color + "55")
    ctx.fillStyle = sphere
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.fill()

    // Subtle shine highlight
    const shine = ctx.createRadialGradient(
      x - radius * 0.3,
      y - radius * 0.4,
      0,
      x - radius * 0.3,
      y - radius * 0.4,
      radius * 0.45
    )
    shine.addColorStop(0, "rgba(255,255,255,0.35)")
    shine.addColorStop(1, "transparent")
    ctx.fillStyle = shine
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.fill()
  }

  const draw2DNode = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    radius: number,
    color: string
  ) => {
    // FLAT 2D - simple filled circle, no gradients
    ctx.globalAlpha = 1

    // Simple flat fill
    ctx.fillStyle = color + "99"
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.fill()

    // Simple 1px border only
    ctx.strokeStyle = color
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.stroke()

    // NO glow, NO gradient, NO shine
    // Completely flat appearance
  }

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

  const externalChange = useRef(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef({
    angleBase: 0,
    expandT: 1, // FIX 1: Keep initial state as Level 1 (spread)
    drillT: 0,
    selectedHub: null as any,
    lastSelectedHub: null as any,
    mouseX: -1000,
    mouseY: -1000,
  });

  useEffect(() => {
    externalChange.current = true;
    
    // Sync graphOpen based on graphLevel
    if (graphLevel === 0 && graphOpen) setGraphOpen(false);
    if (graphLevel > 0 && !graphOpen) setGraphOpen(true);

    // Sync activeHub clear if we go back to level 0 or 1
    if (graphLevel < 2 && activeHub) {
      setActiveHub(null);
      stateRef.current.selectedHub = null;
    }
    
    setTimeout(() => { externalChange.current = false; }, 50);
  }, [graphLevel, graphOpen, activeHub, setGraphOpen, setActiveHub]);

  const prevActiveHub = useRef<string | null>(null);

  useEffect(() => {
    // Only react to new activeHub values
    if (activeHub && activeHub !== prevActiveHub.current) {
      prevActiveHub.current = activeHub;
      
      // If we're not at level 1, go there first
      if (graphLevel < 1) {
        setGraphLevel(1);
        setTimeout(() => {
          const hub = hubNodesRef.current.find(h => h.key.toLowerCase() === activeHub.toLowerCase());
          if (hub) {
            stateRef.current.selectedHub = hub;
            stateRef.current.lastSelectedHub = hub;
          }
          setGraphLevel(2);
        }, 600);
      } else {
        // Already at level 1, drill directly
        const hub = hubNodesRef.current.find(h => h.key.toLowerCase() === activeHub.toLowerCase());
        if (hub) {
          stateRef.current.selectedHub = hub;
          stateRef.current.lastSelectedHub = hub;
        }
        setGraphLevel(2);
      }
    }
    
    // Reset when activeHub is cleared
    if (!activeHub && prevActiveHub.current) {
      prevActiveHub.current = null;
    }
  }, [activeHub, graphLevel, setGraphLevel]);

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

    // Fetch dynamic conversations
    import("../../../services/jarvisApi").then(({ getConversations }) => {
      getConversations().then(data => {
        const convoHub = hubNodesRef.current.find(h => h.key === "conversations");
        if (convoHub) {
          const recent = data.slice(0, 8); // Max 8 leaves for graph
          convoHub.leavesList = recent.map((c: any, i: number) => {
            const angle = (Math.PI * 2 / recent.length) * i;
            let label = c.title || c.preview || "Session";
            if (label.length > 20) label = label.substring(0, 20) + "...";
            return {
              id: "conversations-leaf-" + c.id,
              label,
              color: convoHub.color,
              angle: angle,
              dist: 45 + Math.random() * 35,
              x: 0,
              y: 0,
              vx: 0,
              vy: 0,
            };
          });
        }
      }).catch(err => console.error("Failed to fetch graph convos", err));
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
    let lastDrawMode = graphModeRef.current;
    let lastExpandT = stateRef.current.expandT;
    let lastDrillT = stateRef.current.drillT;

    const draw = () => {
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 600;
      const cx = w / 2;
      const cy = h / 2;

      // GPU OPTIMIZATION: Skip redraw in 2D mode if nothing changed
      const currentMode = graphModeRef.current;
      const currentExpandT = stateRef.current.expandT;
      const currentDrillT = stateRef.current.drillT;
      const isStatic = currentMode === "2d" &&
                       Math.abs(currentExpandT - lastExpandT) < 0.001 &&
                       Math.abs(currentDrillT - lastDrillT) < 0.001 &&
                       lastDrawMode === currentMode;

      if (isStatic) {
        // Nothing changed - skip expensive redraw
        return;
      }

      lastDrawMode = currentMode;
      lastExpandT = currentExpandT;
      lastDrillT = currentDrillT;

      ctx.clearRect(0, 0, w, h);

      // Draw subtle grid in 2D mode
      if (graphModeRef.current === "2d") {
        ctx.strokeStyle = "rgba(82,236,227,0.04)";
        ctx.lineWidth = 0.5;
        const gridSize = 40;
        for (let x = 0; x < w; x += gridSize) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, h);
          ctx.stroke();
        }
        for (let y = 0; y < h; y += gridSize) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(w, y);
          ctx.stroke();
        }
      }

      const { expandT, drillT, selectedHub, lastSelectedHub } = stateRef.current;
      const hubNodes = hubNodesRef.current;
      
      const effectiveHub = selectedHub || lastSelectedHub;

      const drawNode = graphModeRef.current === "3d" ? draw3DNode : draw2DNode;
      const edgeWidth = graphModeRef.current === "3d" ? 1.5 : 0.8;
      const edgeOpacity = graphModeRef.current === "3d" ? 0.7 : 0.4;

      // Outer ring of the core anchor fades out
      ctx.globalAlpha = (1 - drillT) * edgeOpacity;
      if (ctx.globalAlpha > 0.01) {
        ctx.beginPath();
        ctx.arc(cx, cy, 14, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(79, 168, 255, 0.28)";
        ctx.lineWidth = edgeWidth;
        ctx.stroke();
      }
      
      // Core anchor stays permanently bright
      ctx.globalAlpha = 1;
      drawNode(ctx, cx, cy, 9, "#4FA8FF");

      hubNodes.forEach((hub) => {
        const isSelected = effectiveHub === hub;
        const dim = effectiveHub && !isSelected;
        const linkAlpha = Math.max(0, 1 - (dim ? drillT : 0));
        
        ctx.globalAlpha = linkAlpha * edgeOpacity;
        if (ctx.globalAlpha > 0.01) {
          ctx.strokeStyle =
            hub.key === "conversations"
              ? `rgba(255,180,84,${0.25 + expandT * 0.25})`
              : `rgba(79, 168, 255,${0.1 + expandT * 0.22})`;
          ctx.lineWidth = edgeWidth;
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
            const isSelectedHub = effectiveHub === hub;
            const dim = effectiveHub && !isSelectedHub;
            const alpha = Math.max(0, expandT - (dim ? drillT : 0));
            
            ctx.globalAlpha = alpha * edgeOpacity;
            if (ctx.globalAlpha > 0.01) {
              ctx.strokeStyle = `rgba(${hexToRgb(hub.color)},${0.22})`;
              ctx.lineWidth = edgeWidth;
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
            const isSelectedHub = effectiveHub === hub;
            const dim = effectiveHub && !isSelectedHub;
            const alpha = Math.max(0, expandT - (dim ? drillT : 0));
            
            ctx.globalAlpha = alpha;
            if (alpha > 0.01) {
              ctx.globalAlpha = alpha * (graphModeRef.current === "3d" ? 0.8 : 1.0);
              drawNode(ctx, leaf.x, leaf.y, 5, leaf.color);
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
        const isSelected = effectiveHub === hub;
        const dim = effectiveHub && !isSelected;
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
          ctx.lineWidth = edgeWidth;
          ctx.stroke();
        }
        ctx.globalAlpha = alpha;
        drawNode(ctx, hub.x, hub.y, baseR, hub.color);
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
        ctx.fillStyle = "rgba(79, 168, 255, 0.7)";
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
      // Increased to 0.70 per user request so the connecting lines are much longer
      const LEVEL_1_RADIUS = canvasRadius * 0.70;
      
      const { expandT, drillT, selectedHub, lastSelectedHub } = stateRef.current;
      const r = LEVEL_0_RADIUS + (LEVEL_1_RADIUS - LEVEL_0_RADIUS) * expandT;
      const effectiveHub = selectedHub || lastSelectedHub;

      hubNodesRef.current.forEach((hub) => {
        const a = hub.angle + stateRef.current.angleBase;
        
        let targetHubX = cx + Math.cos(a) * r;
        let targetHubY = cy + Math.sin(a) * r;
        
        if (effectiveHub && drillT > 0.01) {
            if (effectiveHub === hub) {
                targetHubX = targetHubX + (cx - targetHubX) * drillT;
                targetHubY = targetHubY + (cy - targetHubY) * drillT;
            } else {
                targetHubX = targetHubX + (targetHubX - cx) * 0.5 * drillT;
                targetHubY = targetHubY + (targetHubY - cy) * 0.5 * drillT;
            }
        }
        
        hub.x = targetHubX;
        hub.y = targetHubY;
        
        const LEAF_ORBIT_RADIUS = canvasRadius * 0.60;
        const LEAF_ORBIT_SPEED = 0.003 * speedMultiplier;

        hub.leavesList.forEach((leaf: any) => {
          if (effectiveHub === hub && drillT > 0.01) {
            // Only rotate in 3D mode - 2D mode is static
            if (graphModeRef.current === "3d") {
              leaf.angle += LEAF_ORBIT_SPEED;
            }
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

        if (stateRef.current.expandT > 0.1) {
          hub.leavesList.forEach((leaf: any) => {
            if (Math.hypot(mx - leaf.x, my - leaf.y) < 30) {
              speedMultiplier = HOVER_SPEED;
              isHovering = true;
            }
          });
        }
      });

      canvas.style.cursor = isHovering ? "pointer" : "default";

      // Only animate in 3D mode - 2D mode is completely static
      if (graphModeRef.current === "3d") {
        stateRef.current.angleBase += 0.0018 * speedMultiplier;
      }

      const targetExpand = graphOpen ? 1 : 0;
      const targetDrill = stateRef.current.selectedHub ? 1 : 0;

      stateRef.current.expandT += (targetExpand - stateRef.current.expandT) * 0.05;
      stateRef.current.drillT += (targetDrill - stateRef.current.drillT) * 0.08;

      layout(speedMultiplier);
      draw();

      // GPU OPTIMIZATION: Adaptive frame rate based on mode
      if (graphModeRef.current === "3d") {
        // 3D mode: 60fps smooth animation
        animationId = requestAnimationFrame(loop);
      } else {
        // 2D mode: 1fps low power mode (draw once per second)
        animationId = window.setTimeout(loop, 1000) as unknown as number;
      }
    };

    // Start the loop
    if (graphModeRef.current === "3d") {
      animationId = requestAnimationFrame(loop);
    } else {
      animationId = window.setTimeout(loop, 1000) as unknown as number;
    }

    return () => {
      window.removeEventListener("resize", sizeCanvas);
      cancelAnimationFrame(animationId);
      clearTimeout(animationId);
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
      let hitLeaf: any = null;
      let bestLeaf = 15;
      stateRef.current.selectedHub.leavesList.forEach((leaf: any) => {
        const d = Math.hypot(leaf.x - mx, leaf.y - my);
        if (d < bestLeaf) {
          hitLeaf = leaf;
          bestLeaf = d;
        }
      });

      if (hitLeaf) {
        if (stateRef.current.selectedHub.key === "conversations") {
          const convoId = hitLeaf.id.replace("conversations-leaf-", "");
          import("../../../services/jarvisApi").then(({ getConversation }) => {
            getConversation(convoId).then((history: any) => {
              if (history && history.length > 0) {
                const store = useConversationStore.getState();
                store.clearConversation();
                store.setConversationId(convoId);
                history
                  .filter((msg: any) => msg.role === "user" || msg.role === "assistant")
                  .forEach((msg: any) => {
                    store.addMessage({
                      id: window.crypto?.randomUUID() || Math.random().toString(),
                      role: msg.role,
                      content: msg.content,
                      timestamp: msg.timestamp || new Date().toISOString()
                    });
                  });
                useAppStore.getState().setGraphOpen(false);
                useAppStore.getState().setChatMode(true);
              }
            });
          });
        }
        return;
      }

      if (mx > 10 && mx < 80 && my > 10 && my < 40) {
        stateRef.current.selectedHub = null;
        setActiveHub(null);
        if (!externalChange.current) setGraphLevel(1);
        return;
      }
      
      if (Math.hypot(mx - cx, my - cy) < 20) {
        stateRef.current.selectedHub = null;
        setActiveHub(null);
        if (!externalChange.current) setGraphLevel(1);
        return;
      }
    } else {
      if (Math.hypot(mx - cx, my - cy) < 15) {
        setGraphOpen(!graphOpen);
        setGraphFocused(true);
        stateRef.current.selectedHub = null;
        setActiveHub(null);
        if (!externalChange.current) setGraphLevel(!graphOpen ? 1 : 0);
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

    if (hit) {
      if (!graphOpen) setGraphOpen(true);
      setGraphFocused(true);
      stateRef.current.selectedHub = hit;
      stateRef.current.lastSelectedHub = hit;
      setActiveHub(hit.key || hit.id);
      if (!externalChange.current) setGraphLevel(2);
    } else {
      if (!stateRef.current.selectedHub) {
          stateRef.current.selectedHub = null;
          setActiveHub(null);
          if (!externalChange.current) setGraphLevel(1);
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
