/* global KeyboardEvent, Element */
import { useEffect } from "react"
import { useAppStore } from "../stores/useAppStore"
import { useAIStore } from "../stores/useAIStore"
import { useConversationStore } from "../stores/useConversationStore"
import { updateSettings } from "../services/jarvisApi"

const PERSONALITY_CYCLE: Array<"assistant" | "developer" | "research"> = [
  "assistant",
  "developer",
  "research",
]

/**
 * True when the focused element is somewhere the user is typing, so we can
 * leave normal text editing alone. Only Ctrl/Cmd+K and Escape are allowed
 * through in that case - every other shortcut is ignored so that e.g.
 * Ctrl+N in a text field keeps whatever meaning the field gives it.
 */
function isTextEntryTarget(el: Element | null): boolean {
  if (!el) return false
  const node = el as HTMLElement
  if (node.isContentEditable) return true
  const tag = node.tagName
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT"
}

export function useGlobalShortcuts() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Ignore synthetic/IME composition keystrokes - firing a shortcut
      // mid-composition would eat characters in non-Latin input.
      if (e.isComposing) return

      const mod = e.ctrlKey || e.metaKey
      const key = e.key.toLowerCase()
      const inTextField = isTextEntryTarget(window.document.activeElement)
      const app = useAppStore.getState()

      // ---- Allowed everywhere, including inside text fields ----

      if (mod && key === "k") {
        e.preventDefault()
        app.setCommandPaletteOpen(!app.commandPaletteOpen)
        return
      }

      if (e.key === "Escape") {
        // 1. Palette wins if it's open (its input has focus at this point,
        //    which is exactly why Escape must bypass the text-field guard).
        if (app.commandPaletteOpen) {
          e.preventDefault()
          app.setCommandPaletteOpen(false)
          return
        }
        // 2. PinAuthModal registers its own Escape handler; don't also
        //    exit chat mode behind it while it's up.
        if (app.deletingConversationId) return
        // 3. Otherwise leave text fields to their own Escape semantics.
        if (inTextField) return
        // 4. Fall through to: leave chat mode, back to the graph view.
        if (app.chatMode) {
          e.preventDefault()
          app.setChatMode(false)
        }
        return
      }

      // ---- Everything below is suppressed while typing ----
      if (inTextField) return

      if (mod && key === "n") {
        e.preventDefault()
        useConversationStore.getState().clearConversation()
        app.setCommandPaletteOpen(false)
        app.showShortcutToast("New conversation")
        return
      }

      if (mod && key === "p") {
        // preventDefault matters here: this would otherwise open the
        // browser/webview print dialog.
        e.preventDefault()
        const ai = useAIStore.getState()
        const idx = PERSONALITY_CYCLE.indexOf(ai.personalityMode)
        const next = PERSONALITY_CYCLE[(idx + 1) % PERSONALITY_CYCLE.length]
        ai.setPersonalityMode(next)
        updateSettings({ personality_mode: next }).catch((err) => {
          console.error("Failed to persist personality mode:", err)
        })
        app.showShortcutToast(`Personality · ${next.toUpperCase()}`)
        return
      }

      if (mod && key === "f") {
        // preventDefault: suppresses the webview's built-in find bar.
        e.preventDefault()
        app.setConversationPanelOpen(true)
        app.requestConversationSearchFocus()
        return
      }
    }

    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])
}
