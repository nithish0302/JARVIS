import { parseUIActions } from "./uiActionParser"
import { describe, it, expect } from "vitest"

describe("parseUIActions", () => {
  it("extracts single action", () => {
    const { cleanText, actions } = parseUIActions(
      "Opening skills. [UI_ACTION:graph_open_hub:Skills]"
    )
    expect(cleanText).toBe("Opening skills.")
    expect(actions).toHaveLength(1)
    expect(actions[0].type).toBe("graph_open_hub")
    expect(actions[0].payload).toBe("Skills")
  })

  it("extracts multiple actions", () => {
    const { cleanText, actions } = parseUIActions(
      "Done. [UI_ACTION:chat_mode_on][UI_ACTION:conversations_open]"
    )
    expect(cleanText).toBe("Done.")
    expect(actions).toHaveLength(2)
  })

  it("returns clean text when no actions", () => {
    const { cleanText, actions } = parseUIActions(
      "Hello, how can I help?"
    )
    expect(cleanText).toBe("Hello, how can I help?")
    expect(actions).toHaveLength(0)
  })
})
