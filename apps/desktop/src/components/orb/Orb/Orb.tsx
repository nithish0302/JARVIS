import { useEffect, useRef } from "react";
import "./Orb.css";
import { cn } from "../../../lib/cn";
import { useAIStore } from "../../../stores/useAIStore";

export function Orb() {
  const { status, provider, model } = useAIStore();

  const orbCoreRef = useRef<HTMLDivElement>(null);
  const orbGlowRef = useRef<HTMLDivElement>(null);
  const audioLevelRef = useRef(0);

  // Convert JARVIS AI status to Orb states
  let orbState = "idle";
  if (status === "streaming" || status === "connecting") {
    orbState = "speaking";
  }
  // Future proofing for voice features
  // if (listening) orbState = "listening";

  const active = orbState === "listening" || orbState === "speaking";

  useEffect(() => {
    let animationFrameId: number;

    const loop = () => {
      const currentActive = orbCoreRef.current?.classList.contains("audio-live") ?? false;
      const target = currentActive ? 0.35 + Math.random() * 0.65 : 0;

      audioLevelRef.current += (target - audioLevelRef.current) * (currentActive ? 0.22 : 0.12);

      if (orbCoreRef.current && orbGlowRef.current) {
        if (currentActive) {
          const scale = 1 + audioLevelRef.current * 0.4;
          orbCoreRef.current.style.transform = `scale(${scale.toFixed(3)})`;
          orbGlowRef.current.style.transform = `scale(${(scale * 1.05).toFixed(3)})`;
        } else {
          orbCoreRef.current.style.transform = "";
          orbGlowRef.current.style.transform = "";
        }
      }

      animationFrameId = requestAnimationFrame(loop);
    };

    animationFrameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  const getStatusLabel = () => {
    if (orbState === "speaking") return "SPEAKING";
    if (orbState === "listening") return "LISTENING";
    return "IDLE";
  };

  const getCaption = () => {
    if (orbState === "speaking") return "speaking...";
    if (orbState === "listening") return "listening, sir...";
    return 'say "jarvis"...';
  };

  return (
    <div className="orb-card !p-[10px_8px_10px]">
      <div className={cn("orb-mini", "active")}>
        <div className="ring ring-outer"></div>
        <div className="ring ring-sweep"></div>
        <div className="ring ring-ticks"></div>
        <div className="ring ring-sweep-inner"></div>
        <div
          className={cn("core-glow", active && "audio-live")}
          ref={orbGlowRef}
        ></div>
        <div
          className={cn("core", active && "audio-live")}
          ref={orbCoreRef}
        >
          <span className="core-text">J.A.R.V.I.S.</span>
        </div>
      </div>
      <div className={cn("orb-status-row", orbState !== "idle" && orbState)}>
        <span className="dot"></span>
        <span className="orb-status">{getStatusLabel()}</span>
      </div>
      <div className="orb-caption">{getCaption()}</div>
      <div className="orb-sub">
        {model} · {provider} fallback
      </div>
    </div>
  );
}
