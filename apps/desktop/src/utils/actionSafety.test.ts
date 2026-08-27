import { describe, it, expect } from "vitest"
import {
  isVoiceSafe,
  needsVoiceConfirmation,
  DESTRUCTIVE_ACTIONS,
  VOICE_CONFIRM_ACTIONS,
  HANDLED_UI_ACTIONS
} from "./actionSafety"

describe("voice allowlist (C1 regression)", () => {
  it("blocks every destructive action from running off a transcript", () => {
    // The old blocklist named only delete_conversation and delete_file,
    // so send_email / create_event / create_github_issue executed
    // immediately from voice. That was C1.
    for (const action of DESTRUCTIVE_ACTIONS) {
      expect(isVoiceSafe(action)).toBe(false)
      expect(needsVoiceConfirmation(action)).toBe(true)
    }
  })

  it("blocks send_email specifically", () => {
    expect(isVoiceSafe("send_email")).toBe(false)
  })

  it("blocks create_github_issue specifically", () => {
    expect(isVoiceSafe("create_github_issue")).toBe(false)
  })

  it("blocks delete_conversation, which the backend does not wrap", () => {
    expect(VOICE_CONFIRM_ACTIONS.has("delete_conversation")).toBe(true)
    expect(isVoiceSafe("delete_conversation")).toBe(false)
  })

  it("treats an unknown action as unsafe by default", () => {
    // The whole point of moving to an allowlist: a future plugin action
    // is non-executable from voice until someone lists it.
    expect(isVoiceSafe("launch_missiles")).toBe(false)
    expect(isVoiceSafe("")).toBe(false)
  })
})

describe("non-destructive voice actions still run immediately", () => {
  const immediate = [
    "check_weather",
    "check_forecast",
    "check_gmail",
    "check_calendar",
    "check_upcoming_events",
    "check_github_repos",
    "check_github_issues",
    "search_github_code",
    "open_app",
    "open_url",
    "system_query",
    "personality_mode",
    "new_chat",
    "graph_open_hub",
    "lock_screen"
  ]

  it.each(immediate)("%s is voice-safe", (action) => {
    expect(isVoiceSafe(action)).toBe(true)
  })

  it("confirm_action itself is voice-safe, or confirmation can never arrive", () => {
    // A backend-rewritten confirm_action tag has to reach the executor to
    // arm pendingCommand. If this were blocked, voice confirmation would
    // deadlock.
    expect(isVoiceSafe("confirm_action")).toBe(true)
  })
})

describe("set consistency", () => {
  it("lists every destructive action as a handled action", () => {
    for (const action of DESTRUCTIVE_ACTIONS) {
      expect(HANDLED_UI_ACTIONS.has(action)).toBe(true)
    }
  })

  it("keeps the two confirmation sets disjoint", () => {
    const overlap = [...DESTRUCTIVE_ACTIONS].filter(a =>
      VOICE_CONFIRM_ACTIONS.has(a)
    )
    expect(overlap).toEqual([])
  })
})
