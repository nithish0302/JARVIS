import { useAppStore } from "../../../stores/useAppStore"

export function ConfirmationButtons() {
  const { pendingCommand, setPendingCommand } = useAppStore()

  if (!pendingCommand) return null

  const handleConfirm = () => {
    // Send "yes" as user message
    const event = new CustomEvent(
      "jarvis-confirm",
      { detail: { response: "yes" } }
    )
    window.dispatchEvent(event)
    setPendingCommand(null)
  }

  const handleCancel = () => {
    setPendingCommand(null)
    const event = new CustomEvent(
      "jarvis-confirm",
      { detail: { response: "no" } }
    )
    window.dispatchEvent(event)
  }

  return (
    <div style={{
      display: "flex",
      gap: "8px",
      padding: "8px 16px",
      justifyContent: "center"
    }}>
      <button
        onClick={handleConfirm}
        style={{
          background: "rgba(239,68,68,0.15)",
          border: "1px solid rgba(239,68,68,0.5)",
          borderRadius: "6px",
          color: "#ef4444",
          padding: "6px 20px",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          cursor: "pointer",
          letterSpacing: "1px"
        }}
      >
        ✓ CONFIRM
      </button>
      <button
        onClick={handleCancel}
        style={{
          background: "rgba(82,236,227,0.08)",
          border: "1px solid rgba(82,236,227,0.2)",
          borderRadius: "6px",
          color: "var(--color-cyan)",
          padding: "6px 20px",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          cursor: "pointer",
          letterSpacing: "1px"
        }}
      >
        ✗ CANCEL
      </button>
    </div>
  )
}
