import { Globe } from "lucide-react"

interface SearchBadgeProps {
  query: string
  visible: boolean
}

export function SearchBadge({ query, visible }: SearchBadgeProps) {
  if (!visible) return null

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        background: "rgba(82,236,227,0.06)",
        border: "1px solid rgba(82,236,227,0.2)",
        borderRadius: "var(--radius-sm, 4px)",
        padding: "3px 8px",
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "10px",
        color: "var(--color-cyan, #52ece3)",
        marginBottom: "4px",
      }}
    >
      <Globe size={10} style={{ marginRight: "4px" }} />
      Searched: "{query}"
    </div>
  )
}
