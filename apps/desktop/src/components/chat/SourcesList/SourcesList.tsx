import { SearchSource } from "../../../types/chat.types"
import { open } from "@tauri-apps/plugin-shell"

interface SourcesListProps {
  sources: SearchSource[]
  visible: boolean
}

export function SourcesList({ sources, visible }: SourcesListProps) {
  if (!visible || sources.length === 0) return null

  const handleSourceClick = async (url: string) => {
    try {
      await open(url)
    } catch {
      window.open(url, "_blank")
    }
  }

  return (
    <div style={{ marginTop: "8px" }}>
      <div style={{ height: "1px", background: "rgba(255,255,255,0.1)", marginBottom: "8px" }} />
      <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "11px", color: "var(--color-text-muted)", marginBottom: "4px" }}>
        Sources:
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {sources.map((src, i) => (
          <div
            key={i}
            onClick={() => handleSourceClick(src.url)}
            style={{
              cursor: "pointer",
              padding: "4px 8px",
              background: "rgba(255,255,255,0.03)",
              borderRadius: "4px",
              borderLeft: "2px solid transparent",
              transition: "all 0.2s ease"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderLeft = "2px solid var(--color-cyan, #52ece3)"
              e.currentTarget.style.background = "rgba(255,255,255,0.06)"
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderLeft = "2px solid transparent"
              e.currentTarget.style.background = "rgba(255,255,255,0.03)"
            }}
          >
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: "11px", color: "var(--color-text-primary, #ffffff)", marginRight: "8px" }}>
              {src.title}
            </span>
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--color-text-muted, rgba(255,255,255,0.5))" }}>
              ({src.source})
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
