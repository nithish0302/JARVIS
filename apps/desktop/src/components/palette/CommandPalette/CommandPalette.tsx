import { useEffect, useMemo, useRef, useState } from "react"
import { createPortal } from "react-dom"
import "./CommandPalette.css"
import { useAppStore } from "../../../stores/useAppStore"
import { useAIStore } from "../../../stores/useAIStore"
import { useConversationStore } from "../../../stores/useConversationStore"
import {
  getConversations,
  getConversation,
  getMemories,
  updateSettings,
} from "../../../services/jarvisApi"
import { HUB_LEAVES } from "../../../data/graphHubs"

type SectionKey = "Conversations" | "Actions" | "Settings" | "Memories" | "Graph"

interface PaletteItem {
  id: string
  section: SectionKey
  label: string
  hint?: string
  /** Extra text matched against the query but shown as a subtitle. */
  detail?: string
  run: () => void
}

/**
 * Subsequence fuzzy match. Returns null for no match, otherwise a score
 * where higher is better. A contiguous substring hit always outranks a
 * scattered subsequence hit, and earlier hits outrank later ones.
 */
function fuzzyScore(query: string, text: string): number | null {
  if (!query) return 0
  const q = query.toLowerCase()
  const t = text.toLowerCase()

  const direct = t.indexOf(q)
  if (direct >= 0) return 10000 - direct

  let cursor = 0
  let score = 0
  let streak = 0
  for (const ch of q) {
    const found = t.indexOf(ch, cursor)
    if (found === -1) return null
    streak = found === cursor ? streak + 1 : 0
    score += 10 + streak * 5 - Math.min(found - cursor, 20)
    cursor = found + 1
  }
  return score
}

const SECTION_ORDER: SectionKey[] = [
  "Conversations",
  "Graph",
  "Actions",
  "Settings",
  "Memories",
]

export function CommandPalette() {
  const open = useAppStore((s) => s.commandPaletteOpen)
  const setOpen = useAppStore((s) => s.setCommandPaletteOpen)

  const [query, setQuery] = useState("")
  const [activeIndex, setActiveIndex] = useState(0)
  const [conversations, setConversations] = useState<any[]>([])
  const [memories, setMemories] = useState<any[]>([])

  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Reset and load fresh data each time the palette opens, so it never
  // shows a stale conversation list from a previous session.
  useEffect(() => {
    if (!open) return
    setQuery("")
    setActiveIndex(0)
    getConversations()
      .then(setConversations)
      .catch(() => setConversations([]))
    // No artificial cap here - the backend already bounds this list
    // (get_all_memories(limit=50)), and now that the graph has real
    // pagination, a palette jump needs the full set to be able to reach
    // (and correctly page to) any memory, not just the first page's worth.
    getMemories()
      .then(setMemories)
      .catch(() => setMemories([]))
    const t = setTimeout(() => inputRef.current?.focus(), 20)
    return () => clearTimeout(t)
  }, [open])

  const items = useMemo<PaletteItem[]>(() => {
    const app = useAppStore.getState()
    const ai = useAIStore.getState()
    const convo = useConversationStore.getState()

    const close = () => setOpen(false)

    const loadConversation = async (id: string, title: string) => {
      try {
        convo.clearConversation()
        const history = await getConversation(id)
        if (!history || history.length === 0) return
        convo.setConversationId(id)
        convo.setConversationTitle(title)
        history
          .filter((m: any) => m.role === "user" || m.role === "assistant")
          .forEach((m: any) => {
            convo.addMessage({
              id: window.crypto?.randomUUID() || Math.random().toString(),
              role: m.role,
              content: m.content,
              timestamp: m.timestamp || new Date().toISOString(),
            })
          })
        app.setChatMode(true)
      } catch (err) {
        console.error("Failed to load conversation", err)
      }
    }

    const setPersonality = (mode: "assistant" | "developer" | "research") => {
      ai.setPersonalityMode(mode)
      updateSettings({ personality_mode: mode }).catch((err) =>
        console.error("Failed to persist personality mode:", err)
      )
      app.showShortcutToast(`Personality · ${mode.toUpperCase()}`)
    }

    const setModifier = (mod: "none" | "planner" | "quiet") => {
      ai.setModifier(mod)
      updateSettings({ modifier: mod }).catch((err) =>
        console.error("Failed to persist modifier:", err)
      )
      app.showShortcutToast(`Modifier · ${mod.toUpperCase()}`)
    }

    // Opens the graph (if closed), drills into the given hub, and tells
    // GraphCanvas which specific leaf to page to and pulse - this is what
    // lets a palette hit reach an item regardless of which page of a
    // hub's real pagination it falls on (e.g. conversations render 12 per
    // page; a jump to item #20 still pages there and finds it for real,
    // no synthetic leaf involved).
    //
    // setActiveHub and setGraphLevel(2) must land together, matching the
    // pattern uiActionExecutor.ts already uses for external hub-selection
    // (graph_open_hub/conversations_open): GraphCanvas has an effect that
    // resets activeHub back to null whenever graphLevel is still < 2 when
    // activeHub changes (it's how canceling out of a hub works) - setting
    // graphLevel synchronously in the same call avoids racing into that
    // reset, which would otherwise leave activeHub null and the Inspector
    // panel blank even though the canvas visually drilled in correctly.
    const jumpToNode = (hub: string, leafId: string) => {
      app.setChatMode(false)
      const focus = () => {
        app.setActiveHub(hub)
        app.setGraphLevel(2)
        app.setFocusLeaf({ hub, leafId })
      }
      if (app.graphLevel === 0 || app.chatMode) {
        app.setGraphLevel(1)
        setTimeout(focus, 800)
      } else {
        focus()
      }
    }

    const list: PaletteItem[] = []

    for (const c of conversations) {
      list.push({
        id: `convo-${c.id}`,
        section: "Conversations",
        label: c.title || "Session",
        detail: c.preview || "",
        run: () => {
          close()
          loadConversation(c.id, c.title || "Session")
        },
      })
    }

    list.push(
      {
        id: "action-new-chat",
        section: "Actions",
        label: "New conversation",
        hint: "Ctrl+N",
        run: () => {
          close()
          convo.clearConversation()
          app.showShortcutToast("New conversation")
        },
      },
      {
        id: "action-toggle-chat-mode",
        section: "Actions",
        label: app.chatMode ? "Exit chat mode (back to graph)" : "Enter chat mode",
        hint: app.chatMode ? "Esc" : undefined,
        run: () => {
          close()
          app.setChatMode(!app.chatMode)
        },
      },
      {
        id: "action-cycle-personality",
        section: "Actions",
        label: "Cycle personality mode",
        detail: `currently ${ai.personalityMode}`,
        hint: "Ctrl+P",
        run: () => {
          close()
          const order: Array<"assistant" | "developer" | "research"> = [
            "assistant",
            "developer",
            "research",
          ]
          const next = order[(order.indexOf(ai.personalityMode) + 1) % order.length]
          setPersonality(next)
        },
      },
      {
        id: "action-open-conversations",
        section: "Actions",
        label: "Open conversation panel",
        hint: "Ctrl+F",
        run: () => {
          close()
          app.setConversationPanelOpen(true)
          app.requestConversationSearchFocus()
        },
      },
      {
        id: "action-toggle-graph",
        section: "Actions",
        label: app.graphOpen ? "Collapse knowledge graph" : "Expand knowledge graph",
        run: () => {
          close()
          app.setGraphOpen(!app.graphOpen)
        },
      }
    )

    list.push(
      {
        id: "settings-open",
        section: "Settings",
        label: app.view === "settings" ? "Close settings" : "Open settings",
        run: () => {
          close()
          app.setView(app.view === "settings" ? "chat" : "settings")
        },
      },
      {
        id: "settings-personality-assistant",
        section: "Settings",
        label: "Personality: Assistant",
        detail: "balanced, professional & warm",
        run: () => {
          close()
          setPersonality("assistant")
        },
      },
      {
        id: "settings-personality-developer",
        section: "Settings",
        label: "Personality: Developer",
        detail: "technical precision, direct tone",
        run: () => {
          close()
          setPersonality("developer")
        },
      },
      {
        id: "settings-personality-research",
        section: "Settings",
        label: "Personality: Research",
        detail: "investigative, deep analysis",
        run: () => {
          close()
          setPersonality("research")
        },
      },
      {
        id: "settings-modifier-none",
        section: "Settings",
        label: "Modifier: None",
        run: () => {
          close()
          setModifier("none")
        },
      },
      {
        id: "settings-modifier-planner",
        section: "Settings",
        label: "Modifier: Planner",
        detail: "structured plans & validation",
        run: () => {
          close()
          setModifier("planner")
        },
      },
      {
        id: "settings-modifier-quiet",
        section: "Settings",
        label: "Modifier: Quiet",
        detail: "ultra-concise, zero filler",
        run: () => {
          close()
          setModifier("quiet")
        },
      }
    )

    for (const m of memories) {
      const content = String(m.content || "")
      if (!content) continue
      list.push({
        id: `memory-${m.id}`,
        section: "Memories",
        label: content.length > 80 ? content.slice(0, 80) + "…" : content,
        detail: `${m.category || "general"} · importance ${m.importance ?? "-"}`,
        run: () => {
          close()
          // There's no memory-detail view in the app yet, so surface the
          // full text in the toast rather than pretending to navigate.
          app.showShortcutToast(content)
        },
      })
    }

    // "Jump to node" - additive section, separate from Conversations/
    // Memories above (which keep their existing load-into-chat / toast
    // behavior untouched). Every entry here does one thing: open the
    // graph to the matching hub with that exact leaf pulsing, so a
    // specific item can always be found by name even in a cluttered or
    // paginated hub.
    for (const c of conversations) {
      const title = c.title || "Session"
      list.push({
        id: `graph-conversation-${c.id}`,
        section: "Graph",
        label: title,
        detail: "Conversations node",
        run: () => {
          close()
          jumpToNode("conversations", `conversations-leaf-${c.id}`)
        },
      })
    }

    for (const m of memories) {
      const content = String(m.content || "")
      if (!content) continue
      list.push({
        id: `graph-memory-${m.id}`,
        section: "Graph",
        label: content.length > 60 ? content.slice(0, 60) + "…" : content,
        detail: "Memories node",
        run: () => {
          close()
          jumpToNode("memories", `memories-leaf-${m.id}`)
        },
      })
    }

    HUB_LEAVES.files.forEach((fileLabel, i) => {
      list.push({
        id: `graph-file-${i}`,
        section: "Graph",
        label: fileLabel,
        detail: "Files node",
        run: () => {
          close()
          jumpToNode("files", `files-leaf-${i}`)
        },
      })
    })

    return list
  }, [conversations, memories, setOpen])

  const filtered = useMemo(() => {
    const scored: Array<{ item: PaletteItem; score: number }> = []
    for (const item of items) {
      const haystack = `${item.label} ${item.detail || ""}`
      const score = fuzzyScore(query.trim(), haystack)
      if (score !== null) scored.push({ item, score })
    }
    if (query.trim()) scored.sort((a, b) => b.score - a.score)
    return scored.map((s) => s.item)
  }, [items, query])

  // Group while preserving the (possibly score-sorted) order within each
  // section, so results stay visually grouped and labeled.
  const grouped = useMemo(() => {
    const out: Array<{ section: SectionKey; items: PaletteItem[] }> = []
    for (const section of SECTION_ORDER) {
      const inSection = filtered.filter((i) => i.section === section)
      if (inSection.length) out.push({ section, items: inSection })
    }
    return out
  }, [filtered])

  const flat = useMemo(() => grouped.flatMap((g) => g.items), [grouped])

  useEffect(() => {
    setActiveIndex((i) => (flat.length === 0 ? 0 : Math.min(i, flat.length - 1)))
  }, [flat.length])

  // Keep the highlighted row scrolled into view during arrow navigation.
  useEffect(() => {
    if (!open) return
    const el = listRef.current?.querySelector<HTMLDivElement>(
      `[data-index="${activeIndex}"]`
    )
    // Guarded: scrollIntoView is absent in jsdom and not guaranteed in
    // every webview; losing auto-scroll is fine, throwing is not.
    if (typeof el?.scrollIntoView === "function") {
      el.scrollIntoView({ block: "nearest" })
    }
  }, [activeIndex, open])

  if (!open) return null

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setActiveIndex((i) => (flat.length ? (i + 1) % flat.length : 0))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActiveIndex((i) => (flat.length ? (i - 1 + flat.length) % flat.length : 0))
    } else if (e.key === "Enter") {
      e.preventDefault()
      flat[activeIndex]?.run()
    }
    // Escape is handled by useGlobalShortcuts so there's a single owner.
  }

  return createPortal(
    <div className="cmdk-backdrop" onClick={() => setOpen(false)}>
      <div
        className="cmdk-panel"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Command palette"
        aria-modal="true"
      >
        <div className="cmdk-corner tl" />
        <div className="cmdk-corner tr" />
        <div className="cmdk-corner bl" />
        <div className="cmdk-corner br" />
        <div className="cmdk-scanline" />

        <div className="cmdk-search">
          <span className="cmdk-prompt">&gt;</span>
          <input
            ref={inputRef}
            className="cmdk-input"
            placeholder="Search conversations, actions, settings…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setActiveIndex(0)
            }}
            onKeyDown={onKeyDown}
            aria-label="Command palette search"
          />
          <span className="cmdk-badge">ESC</span>
        </div>

        <div className="cmdk-divider" />

        <div className="cmdk-list" ref={listRef}>
          {flat.length === 0 ? (
            <div className="cmdk-empty">No results</div>
          ) : (
            grouped.map((group) => (
              <div className="cmdk-group" key={group.section}>
                <div className="cmdk-group-label">{group.section}</div>
                {group.items.map((item) => {
                  const index = flat.indexOf(item)
                  return (
                    <div
                      key={item.id}
                      data-index={index}
                      className={`cmdk-item${index === activeIndex ? " active" : ""}`}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => item.run()}
                    >
                      <div className="cmdk-item-text">
                        <span className="cmdk-item-label">{item.label}</span>
                        {item.detail ? (
                          <span className="cmdk-item-detail">{item.detail}</span>
                        ) : null}
                      </div>
                      {item.hint ? (
                        <span className="cmdk-item-hint">{item.hint}</span>
                      ) : null}
                    </div>
                  )
                })}
              </div>
            ))
          )}
        </div>

        <div className="cmdk-footer">
          <span>↑↓ navigate</span>
          <span>⏎ select</span>
          <span>esc close</span>
        </div>
      </div>
    </div>,
    window.document.body
  )
}
