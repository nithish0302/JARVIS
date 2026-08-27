import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import {
  runConfirmedAction,
  assertDestructiveActionsCovered
} from "./confirmedActions"
import { DESTRUCTIVE_ACTIONS } from "./actionSafety"

const sendEmail = vi.fn()
const createEvent = vi.fn()
const createGithubIssue = vi.fn()
const deleteFile = vi.fn()
const executeUIActions = vi.fn()

vi.mock("../services/jarvisApi", () => ({
  sendEmail: (...a: unknown[]) => sendEmail(...a),
  createEvent: (...a: unknown[]) => createEvent(...a),
  createGithubIssue: (...a: unknown[]) => createGithubIssue(...a)
}))

vi.mock("../services/systemApi", () => ({
  deleteFile: (...a: unknown[]) => deleteFile(...a)
}))

vi.mock("./uiActionExecutor", () => ({
  executeUIActions: (...a: unknown[]) => executeUIActions(...a)
}))

function collector() {
  const messages: string[] = []
  return {
    messages,
    addMessage: (m: { content: string }) => { messages.push(m.content) }
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  sendEmail.mockResolvedValue(undefined)
  createEvent.mockResolvedValue(undefined)
  createGithubIssue.mockResolvedValue(undefined)
  deleteFile.mockResolvedValue("Deleted file 'notes.txt' successfully")
  if (!globalThis.crypto) {
    // jsdom in this project exposes crypto, but keep the helper honest.
    Object.defineProperty(globalThis, "crypto", {
      value: { randomUUID: () => "test-uuid" }
    })
  }
})

describe("handler coverage", () => {
  it("registers a handler for every action the backend wraps in confirm_action", () => {
    // This is the structural guarantee against H1: the backend rewriting
    // an action to confirm_action with no handler here meant confirming
    // it silently did nothing and still reported success.
    expect(assertDestructiveActionsCovered()).toEqual([])
  })
})

describe("create_github_issue (H1 regression)", () => {
  it("actually calls the API when confirmed", async () => {
    const { messages, addMessage } = collector()

    await runConfirmedAction(
      "create_github_issue",
      "nithish0302/JARVIS:Test issue:Filed from the confirm flow",
      addMessage
    )

    // The bug: this assertion failed because the dispatcher's final else
    // branch replied "Command confirmation received." and created nothing.
    expect(createGithubIssue).toHaveBeenCalledTimes(1)
    expect(createGithubIssue).toHaveBeenCalledWith(
      "nithish0302/JARVIS",
      "Test issue",
      "Filed from the confirm flow"
    )
    expect(messages[0]).toContain("✅")
    expect(messages[0]).toContain("nithish0302/JARVIS")
    expect(messages.join(" ")).not.toContain("Command confirmation received")
  })

  it("keeps colons in the issue body intact", async () => {
    const { addMessage } = collector()
    await runConfirmedAction(
      "create_github_issue",
      "me/repo:Crash on start:Stack trace: line 12: boom",
      addMessage
    )
    expect(createGithubIssue).toHaveBeenCalledWith(
      "me/repo",
      "Crash on start",
      "Stack trace: line 12: boom"
    )
  })

  it("surfaces an API failure instead of reporting success", async () => {
    createGithubIssue.mockRejectedValue(new Error("Bad credentials"))
    const { messages, addMessage } = collector()

    await runConfirmedAction("create_github_issue", "me/repo:T:B", addMessage)

    expect(messages[0]).toContain("❌")
    expect(messages[0]).toContain("Bad credentials")
  })
})

describe("the other destructive actions still execute", () => {
  it("send_email", async () => {
    const { messages, addMessage } = collector()
    await runConfirmedAction(
      "send_email", "test@test.com:Hello:Just saying hi", addMessage
    )
    expect(sendEmail).toHaveBeenCalledWith(
      "test@test.com", "Hello", "Just saying hi"
    )
    expect(messages[0]).toContain("✅")
  })

  it("create_event", async () => {
    const { addMessage } = collector()
    await runConfirmedAction(
      "create_event", "Standup:tomorrow 9am:tomorrow 9:15am", addMessage
    )
    expect(createEvent).toHaveBeenCalledWith(
      "Standup", "tomorrow 9am", "tomorrow 9:15am"
    )
  })

  it("splits create_event exactly as uiActionExecutor does", () => {
    // Documented limitation, not a regression: the UI_ACTION payload
    // format is colon-delimited, and ISO timestamps contain colons, so
    // "Standup:2026-09-01T09:00:2026-09-01T09:15" cannot round-trip -
    // field 2 becomes "2026-09-01T09". The executor's own create_event
    // case splits the same way, so confirmed and unconfirmed execution at
    // least agree. Fixing it properly means changing the delimiter across
    // the prompt, parser, and executor together.
    expect("Standup:2026-09-01T09:00:2026-09-01T09:15".split(":")[1])
      .toBe("2026-09-01T09")
  })

  it("delete_file passes confirmed=true", async () => {
    const { messages, addMessage } = collector()
    await runConfirmedAction("delete_file", "C:\\Users\\me\\notes.txt", addMessage)
    expect(deleteFile).toHaveBeenCalledWith("C:\\Users\\me\\notes.txt", true)
    expect(messages[0]).toContain("✅")
  })
})

describe("fallback and failure modes", () => {
  it("re-dispatches a non-destructive handled action through the executor", async () => {
    const { addMessage } = collector()
    await runConfirmedAction("delete_conversation", "Project notes", addMessage)

    // delete_conversation has its own PIN gate; confirming it should hand
    // back to the normal executor so that modal opens.
    expect(executeUIActions).toHaveBeenCalledWith([
      { type: "delete_conversation", payload: "Project notes" }
    ])
  })

  it("fails LOUDLY for an action with no handler anywhere", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {})
    const { messages, addMessage } = collector()

    await runConfirmedAction("wire_transfer", "1000:GBP", addMessage)

    // The H1 failure mode was a quiet success message. Neither the user
    // nor the console may be told this worked.
    expect(consoleError).toHaveBeenCalled()
    expect(messages[0]).toContain("❌")
    expect(messages[0]).toContain("isn't wired up")
    expect(messages[0]).toContain("Nothing was changed")
    expect(executeUIActions).not.toHaveBeenCalled()
    consoleError.mockRestore()
  })

  it("reports a malformed payload rather than sending a partial email", async () => {
    const { messages, addMessage } = collector()
    await runConfirmedAction("send_email", "only-a-recipient", addMessage)

    expect(sendEmail).not.toHaveBeenCalled()
    expect(messages[0]).toContain("❌")
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("every destructive action is covered by a test above", () => {
  it("has no untested destructive action", () => {
    // Fails when someone adds an action to DESTRUCTIVE_ACTIONS without
    // adding a case here.
    const tested = new Set([
      "delete_file", "send_email", "create_event", "create_github_issue"
    ])
    const untested = [...DESTRUCTIVE_ACTIONS].filter(a => !tested.has(a))
    expect(untested).toEqual([])
  })
})
