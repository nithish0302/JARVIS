import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CommandPalette } from "./CommandPalette";
import { useAppStore } from "../../../stores/useAppStore";

vi.mock("../../../services/jarvisApi", () => ({
  getConversations: vi.fn().mockResolvedValue([
    { id: "c1", title: "Rust ownership notes", preview: "borrow checker", updated_at: "" },
    { id: "c2", title: "Grocery list", preview: "milk", updated_at: "" },
  ]),
  getConversation: vi.fn().mockResolvedValue([]),
  getMemories: vi.fn().mockResolvedValue([
    { id: "m1", content: "User prefers dark mode", category: "preference", importance: 8 },
  ]),
  updateSettings: vi.fn().mockResolvedValue({}),
}));

describe("CommandPalette", () => {
  beforeEach(() => {
    useAppStore.setState({ commandPaletteOpen: false, chatMode: false });
  });

  it("renders nothing when closed", () => {
    render(<CommandPalette />);
    expect(screen.queryByLabelText("Command palette search")).toBeNull();
  });

  it("renders grouped, labeled sections when open", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    render(<CommandPalette />);
    expect(await screen.findByText("Conversations")).toBeInTheDocument();
    expect(screen.getByText("Graph")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(await screen.findByText("Memories")).toBeInTheDocument();
  });

  it("shows keyboard hints next to actions that have one", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    render(<CommandPalette />);
    expect(await screen.findByText("New conversation")).toBeInTheDocument();
    expect(screen.getByText("Ctrl+N")).toBeInTheDocument();
    expect(screen.getByText("Ctrl+P")).toBeInTheDocument();
  });

  it("fuzzy-matches conversation titles", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    render(<CommandPalette />);
    const input = await screen.findByLabelText("Command palette search");
    fireEvent.change(input, { target: { value: "rust" } });
    await waitFor(() => {
      // Appears twice by design: once as a Conversations entry (loads it
      // into chat) and once as a Graph entry (jumps to its graph node) -
      // see the "Graph section" tests below for that second one.
      expect(screen.getAllByText("Rust ownership notes")).toHaveLength(2);
    });
    expect(screen.queryByText("Grocery list")).toBeNull();
  });

  it("matches non-contiguous subsequences", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    render(<CommandPalette />);
    const input = await screen.findByLabelText("Command palette search");
    // "rsown" is a subsequence of "Rust ownership notes"
    fireEvent.change(input, { target: { value: "rsown" } });
    await waitFor(() => {
      expect(screen.getAllByText("Rust ownership notes").length).toBeGreaterThan(0);
    });
  });

  it("shows a No results line when nothing matches", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    render(<CommandPalette />);
    const input = await screen.findByLabelText("Command palette search");
    fireEvent.change(input, { target: { value: "zzzzqqqq" } });
    await waitFor(() => {
      expect(screen.getByText("No results")).toBeInTheDocument();
    });
  });

  it("Enter runs the highlighted item", async () => {
    useAppStore.setState({ commandPaletteOpen: true, chatMode: false });
    render(<CommandPalette />);
    const input = await screen.findByLabelText("Command palette search");
    fireEvent.change(input, { target: { value: "enter chat mode" } });
    await waitFor(() => {
      expect(screen.getByText("Enter chat mode")).toBeInTheDocument();
    });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(useAppStore.getState().chatMode).toBe(true);
      expect(useAppStore.getState().commandPaletteOpen).toBe(false);
    });
  });

  it("ArrowDown moves the highlight to the next item", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    // Note: the palette portals into document.body, so queries must go
    // against the document rather than render()'s container element.
    render(<CommandPalette />);
    const container = document.body;
    const input = await screen.findByLabelText("Command palette search");
    await waitFor(() => {
      expect(container.querySelectorAll(".cmdk-item").length).toBeGreaterThan(1);
    });
    expect(container.querySelector(".cmdk-item.active")?.getAttribute("data-index")).toBe("0");
    fireEvent.keyDown(input, { key: "ArrowDown" });
    await waitFor(() => {
      expect(container.querySelector(".cmdk-item.active")?.getAttribute("data-index")).toBe("1");
    });
  });

  it("Graph section entry jumps to the matching hub and leaf", async () => {
    useAppStore.setState({
      commandPaletteOpen: true,
      activeHub: null,
      focusLeaf: null,
      graphOpen: false,
    });
    render(<CommandPalette />);
    const input = await screen.findByLabelText("Command palette search");
    fireEvent.change(input, { target: { value: "Conversations node" } });
    const entry = await screen.findByText("Rust ownership notes");
    fireEvent.click(entry);

    await waitFor(() => {
      expect(useAppStore.getState().commandPaletteOpen).toBe(false);
    });
    expect(useAppStore.getState().activeHub).toBe("conversations");
    expect(useAppStore.getState().focusLeaf).toEqual({
      hub: "conversations",
      leafId: "conversations-leaf-c1",
    });
    // Unlike a Conversations-section click, this must NOT load the
    // conversation into chat mode - it's a graph jump, not a chat load.
    expect(useAppStore.getState().chatMode).toBe(false);
  });

  it("Graph section entries exist for memories and files too", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    render(<CommandPalette />);
    const input = await screen.findByLabelText("Command palette search");

    fireEvent.change(input, { target: { value: "Memories node" } });
    expect(await screen.findByText("User prefers dark mode")).toBeInTheDocument();

    fireEvent.change(input, { target: { value: "Files node" } });
    expect(await screen.findByText("Documents")).toBeInTheDocument();
  });

  it("ArrowUp from the first item wraps to the last", async () => {
    useAppStore.setState({ commandPaletteOpen: true });
    // Note: the palette portals into document.body, so queries must go
    // against the document rather than render()'s container element.
    render(<CommandPalette />);
    const container = document.body;
    const input = await screen.findByLabelText("Command palette search");
    await waitFor(() => {
      expect(container.querySelectorAll(".cmdk-item").length).toBeGreaterThan(1);
    });
    const count = container.querySelectorAll(".cmdk-item").length;
    fireEvent.keyDown(input, { key: "ArrowUp" });
    await waitFor(() => {
      expect(
        container.querySelector(".cmdk-item.active")?.getAttribute("data-index")
      ).toBe(String(count - 1));
    });
  });
});
