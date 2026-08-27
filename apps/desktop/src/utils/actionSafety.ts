/**
 * Single source of truth for which UI actions are safe to execute
 * without an explicit confirmation, and which are safe to execute
 * straight off a voice transcript.
 *
 * This file exists because the previous arrangement spread that decision
 * across three places that had to be kept in sync by hand, and they
 * drifted twice:
 *
 *   - The backend rewrote `create_github_issue` to `confirm_action`, but
 *     useJarvisChat's confirmation dispatcher had no branch for it, so
 *     confirming did nothing and reported success anyway.
 *   - The voice path used a *blocklist* of two actions, so every action
 *     added afterwards (send_email, create_event, create_github_issue)
 *     was executable from a raw transcript by default.
 *
 * Both bugs share one cause: adding an action required remembering to
 * update code somewhere else. Everything here is derived rather than
 * restated, so the default for anything new is "unsafe until listed".
 */

/**
 * Every action `uiActionExecutor.ts` actually implements a case for.
 *
 * Anything not in this set falls through the executor's `default:` and is
 * silently ignored, so we check against it before dispatching and fail
 * loudly instead.
 */
export const HANDLED_UI_ACTIONS: ReadonlySet<string> = new Set([
  // chat / conversation
  "chat_mode_on",
  "chat_mode_off",
  "new_chat",
  "open_chat",
  "rename_chat",
  "delete_conversation",
  "conversations_open",
  "conversations_close",
  // graph
  "graph_expand",
  "graph_collapse",
  "graph_open_hub",
  // settings / providers
  "switch_provider",
  "personality_mode",
  "modifier",
  "provider_override",
  "fallback_mode",
  "address_preference",
  // desktop automation
  "open_app",
  "open_url",
  "close_app",
  "set_volume",
  "lock_screen",
  "system_query",
  // filesystem
  "list_dir",
  "create_folder",
  "open_file",
  "show_explorer",
  "delete_file",
  // confirmation mechanism itself
  "confirm_action",
  // gmail
  "check_gmail",
  "search_gmail",
  "send_email",
  // calendar
  "check_calendar",
  "check_upcoming_events",
  "create_event",
  // weather
  "check_weather",
  "check_forecast",
  // github
  "check_github_repos",
  "check_github_issues",
  "search_github_issues",
  "create_github_issue",
  "check_github_prs",
  "check_pr_status",
  "search_github_code",
])

/**
 * Actions the backend rewrites to `confirm_action:<type>:<payload>`.
 *
 * MIRRORS `DESTRUCTIVE_UI_ACTIONS` in
 * `services/jarvis-engine/src/jarvis_engine/api/routes.py`. Keep the two
 * in sync — the backend decides what gets wrapped, this set decides what
 * the UI treats as needing a handler.
 */
export const DESTRUCTIVE_ACTIONS: ReadonlySet<string> = new Set([
  "delete_file",
  "send_email",
  "create_event",
  "create_github_issue",
])

/**
 * Actions the backend does NOT wrap, but which still must not run
 * straight off a voice transcript.
 *
 * `delete_conversation` has its own server-side PIN gate, so it needs no
 * confirm wrapper in chat — but "delete the notes conversation" is well
 * within the range of things speech recognition invents, so voice routes
 * it through confirmation first and the PIN modal second.
 */
export const VOICE_CONFIRM_ACTIONS: ReadonlySet<string> = new Set([
  "delete_conversation",
])

/**
 * True when an action may execute immediately from a voice transcript.
 *
 * Allowlist, not blocklist: an action qualifies only by being a known
 * handled action that is on neither confirmation list. A new plugin
 * action is therefore non-executable from voice until someone adds it to
 * HANDLED_UI_ACTIONS, which is the moment they're looking at this file
 * and its two confirmation sets.
 */
export function isVoiceSafe(actionType: string): boolean {
  return (
    HANDLED_UI_ACTIONS.has(actionType) &&
    !DESTRUCTIVE_ACTIONS.has(actionType) &&
    !VOICE_CONFIRM_ACTIONS.has(actionType)
  )
}

/** True when an action needs a confirmation step before it runs from voice. */
export function needsVoiceConfirmation(actionType: string): boolean {
  return !isVoiceSafe(actionType)
}
