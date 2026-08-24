/* global KeyboardEvent */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useGlobalShortcuts } from "./useGlobalShortcuts";
import { useAppStore } from "../stores/useAppStore";
import { useAIStore } from "../stores/useAIStore";
import { useConversationStore } from "../stores/useConversationStore";

vi.mock("../services/jarvisApi", () => ({
  updateSettings: vi.fn().mockResolvedValue({}),
}));

/** Dispatch a keydown from a specific element so activeElement matters. */
function press(
  key: string,
  opts: { ctrl?: boolean; from?: HTMLElement } = {}
) {
  const target = opts.from ?? document.body;
  target.focus();
  const event = new KeyboardEvent("keydown", {
    key,
    ctrlKey: opts.ctrl ?? false,
    bubbles: true,
    cancelable: true,
  });
  window.dispatchEvent(event);
  return event;
}

function mountInput(tag: "input" | "textarea" = "input") {
  const el = document.createElement(tag);
  document.body.appendChild(el);
  return el as HTMLElement;
}

describe("useGlobalShortcuts", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    useAppStore.setState({
      commandPaletteOpen: false,
      chatMode: false,
      conversationPanelOpen: false,
      deletingConversationId: null,
      conversationSearchFocusToken: 0,
    });
    useAIStore.setState({ personalityMode: "assistant" });
    useConversationStore.setState({ currentConversationId: "abc", messages: [] });
  });

  it("Ctrl+K opens the palette from anywhere", () => {
    renderHook(() => useGlobalShortcuts());
    press("k", { ctrl: true });
    expect(useAppStore.getState().commandPaletteOpen).toBe(true);
  });

  it("Ctrl+K still works while typing in an input", () => {
    renderHook(() => useGlobalShortcuts());
    press("k", { ctrl: true, from: mountInput() });
    expect(useAppStore.getState().commandPaletteOpen).toBe(true);
  });

  it("Ctrl+N starts a new conversation", () => {
    renderHook(() => useGlobalShortcuts());
    press("n", { ctrl: true });
    expect(useConversationStore.getState().currentConversationId).toBeNull();
  });

  it("Ctrl+N is ignored while typing in an input", () => {
    renderHook(() => useGlobalShortcuts());
    press("n", { ctrl: true, from: mountInput() });
    expect(useConversationStore.getState().currentConversationId).toBe("abc");
  });

  it("Ctrl+N is ignored while typing in a textarea", () => {
    renderHook(() => useGlobalShortcuts());
    press("n", { ctrl: true, from: mountInput("textarea") });
    expect(useConversationStore.getState().currentConversationId).toBe("abc");
  });

  it("Ctrl+N is ignored inside a contenteditable", () => {
    renderHook(() => useGlobalShortcuts());
    const div = document.createElement("div");
    div.setAttribute("contenteditable", "true");
    div.tabIndex = 0;
    // jsdom doesn't implement isContentEditable off the attribute
    Object.defineProperty(div, "isContentEditable", { value: true });
    document.body.appendChild(div);
    press("n", { ctrl: true, from: div });
    expect(useConversationStore.getState().currentConversationId).toBe("abc");
  });

  it("Ctrl+P cycles personality assistant -> developer", () => {
    renderHook(() => useGlobalShortcuts());
    press("p", { ctrl: true });
    expect(useAIStore.getState().personalityMode).toBe("developer");
  });

  it("Ctrl+P wraps research -> assistant", () => {
    useAIStore.setState({ personalityMode: "research" });
    renderHook(() => useGlobalShortcuts());
    press("p", { ctrl: true });
    expect(useAIStore.getState().personalityMode).toBe("assistant");
  });

  it("Ctrl+P is ignored while typing", () => {
    renderHook(() => useGlobalShortcuts());
    press("p", { ctrl: true, from: mountInput() });
    expect(useAIStore.getState().personalityMode).toBe("assistant");
  });

  it("Ctrl+F opens the conversation panel and requests search focus", () => {
    renderHook(() => useGlobalShortcuts());
    press("f", { ctrl: true });
    const s = useAppStore.getState();
    expect(s.conversationPanelOpen).toBe(true);
    expect(s.conversationSearchFocusToken).toBe(1);
  });

  it("Ctrl+F is ignored while typing", () => {
    renderHook(() => useGlobalShortcuts());
    press("f", { ctrl: true, from: mountInput() });
    expect(useAppStore.getState().conversationPanelOpen).toBe(false);
  });

  it("Escape closes the palette before touching chat mode", () => {
    useAppStore.setState({ commandPaletteOpen: true, chatMode: true });
    renderHook(() => useGlobalShortcuts());
    press("Escape");
    const s = useAppStore.getState();
    expect(s.commandPaletteOpen).toBe(false);
    expect(s.chatMode).toBe(true);
  });

  it("Escape exits chat mode when the palette is closed", () => {
    useAppStore.setState({ chatMode: true });
    renderHook(() => useGlobalShortcuts());
    press("Escape");
    expect(useAppStore.getState().chatMode).toBe(false);
  });

  it("Escape closes the palette even when focus is in its input", () => {
    useAppStore.setState({ commandPaletteOpen: true });
    renderHook(() => useGlobalShortcuts());
    press("Escape", { from: mountInput() });
    expect(useAppStore.getState().commandPaletteOpen).toBe(false);
  });

  it("Escape does not exit chat mode while typing in an input", () => {
    useAppStore.setState({ chatMode: true });
    renderHook(() => useGlobalShortcuts());
    press("Escape", { from: mountInput() });
    expect(useAppStore.getState().chatMode).toBe(true);
  });

  it("Escape defers to PinAuthModal while a delete confirm is open", () => {
    useAppStore.setState({ chatMode: true, deletingConversationId: "xyz" });
    renderHook(() => useGlobalShortcuts());
    press("Escape");
    expect(useAppStore.getState().chatMode).toBe(true);
  });

  it("plain letters never trigger shortcuts", () => {
    renderHook(() => useGlobalShortcuts());
    press("n");
    press("k");
    press("p");
    const s = useAppStore.getState();
    expect(s.commandPaletteOpen).toBe(false);
    expect(useConversationStore.getState().currentConversationId).toBe("abc");
    expect(useAIStore.getState().personalityMode).toBe("assistant");
  });
});
