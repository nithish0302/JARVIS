/**
 * Execution of an action the user has explicitly confirmed.
 *
 * Replaces the `if (cmdType === "delete_file") ... else if ... else` chain
 * that used to live inline in useJarvisChat. That chain had a branch for
 * three of the four actions the backend wraps in `confirm_action`, and its
 * final `else` reported "Command confirmation received." — so confirming a
 * GitHub issue told the user it worked and created nothing.
 *
 * Two things prevent that here: the dispatch is a lookup rather than a
 * chain, and `assertDestructiveActionsCovered()` fails loudly at module
 * load if any action the backend wraps has no handler registered.
 */
import type { Message } from "../types/chat.types"
import { DESTRUCTIVE_ACTIONS, HANDLED_UI_ACTIONS } from "./actionSafety"
import { executeUIActions } from "./uiActionExecutor"

type AddMessage = (message: Message) => void

/** A handler runs the action and resolves with the line to show the user. */
type ConfirmHandler = (payload: string) => Promise<string>

function timestamp(): string {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  })
}

function say(addMessage: AddMessage, content: string): void {
  addMessage({
    id: window.crypto.randomUUID(),
    role: "assistant",
    content,
    timestamp: timestamp()
  })
}

/**
 * Splits `a:b:rest` into exactly `count` fields, with the final field
 * absorbing any remaining colons (subject lines and issue bodies contain
 * them routinely). Returns null when there aren't enough fields.
 */
function splitPayload(payload: string, count: number): string[] | null {
  const parts = payload.split(":")
  if (parts.length < count) return null
  return [
    ...parts.slice(0, count - 1),
    parts.slice(count - 1).join(":")
  ]
}

/**
 * Handlers for every action in DESTRUCTIVE_ACTIONS.
 *
 * Anything confirmed that isn't listed here falls back to the normal
 * executor (see runConfirmedAction), which is correct for actions that
 * carry their own second gate — delete_conversation's PIN modal, for
 * instance. delete_file needs an explicit handler precisely because its
 * executor case re-arms the confirmation instead of executing.
 */
const CONFIRM_HANDLERS: Record<string, ConfirmHandler> = {
  delete_file: async (path) => {
    const systemApi = await import("../services/systemApi")
    return await systemApi.deleteFile(path, true)
  },

  send_email: async (payload) => {
    const fields = splitPayload(payload, 3)
    if (!fields) throw new Error(`Malformed send_email payload: "${payload}"`)
    const [to, subject, body] = fields
    const api = await import("../services/jarvisApi")
    await api.sendEmail(to, subject, body)
    return `Email sent to ${to}.`
  },

  create_event: async (payload) => {
    const fields = splitPayload(payload, 3)
    if (!fields) throw new Error(`Malformed create_event payload: "${payload}"`)
    const [title, start, end] = fields
    const api = await import("../services/jarvisApi")
    await api.createEvent(title, start, end)
    return `Calendar event "${title}" created.`
  },

  // The handler whose absence was H1.
  create_github_issue: async (payload) => {
    const fields = splitPayload(payload, 3)
    if (!fields) {
      throw new Error(`Malformed create_github_issue payload: "${payload}"`)
    }
    const [repo, title, body] = fields
    const api = await import("../services/jarvisApi")
    await api.createGithubIssue(repo, title, body)
    return `GitHub issue "${title}" created in ${repo}.`
  }
}

/**
 * Every action the backend wraps in `confirm_action` must have a handler,
 * or confirming it silently does nothing. Checked at module load so the
 * failure surfaces on app start rather than the first time a user
 * confirms one in production.
 */
export function assertDestructiveActionsCovered(): string[] {
  const missing = [...DESTRUCTIVE_ACTIONS].filter(
    (action) => !(action in CONFIRM_HANDLERS)
  )
  if (missing.length > 0) {
    console.error(
      "[JARVIS] Destructive actions with no confirmation handler — " +
      "confirming these would silently do nothing:",
      missing
    )
  }
  return missing
}

assertDestructiveActionsCovered()

/**
 * Runs a confirmed action and reports the outcome in the chat transcript.
 *
 * Resolution order:
 *   1. An explicit handler in CONFIRM_HANDLERS.
 *   2. Any other action the executor implements — re-dispatched normally,
 *      which is how a confirmed delete_conversation reaches its PIN modal
 *      and how a future plugin action works with no changes here.
 *   3. Anything else: reported as an error, to the user and the console.
 *      Never a quiet success.
 */
export async function runConfirmedAction(
  actionType: string,
  payload: string,
  addMessage: AddMessage
): Promise<void> {
  const handler = CONFIRM_HANDLERS[actionType]

  if (handler) {
    try {
      const result = await handler(payload)
      say(addMessage, `✅ ${result}`)
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message
        : typeof err === "string" ? err
        : "Unknown error occurred"
      console.error(`[JARVIS] Confirmed ${actionType} failed:`, err)
      say(addMessage, `❌ ${message}`)
    }
    return
  }

  if (HANDLED_UI_ACTIONS.has(actionType)) {
    executeUIActions([{ type: actionType, payload: payload || undefined }])
    return
  }

  console.error(
    `[JARVIS] Confirmed action "${actionType}" has no handler and is not ` +
    `implemented in uiActionExecutor. Payload: "${payload}". ` +
    `Add it to HANDLED_UI_ACTIONS and/or CONFIRM_HANDLERS.`
  )
  say(
    addMessage,
    `❌ I can't carry out "${actionType}" — it isn't wired up yet. ` +
    `Nothing was changed.`
  )
}
