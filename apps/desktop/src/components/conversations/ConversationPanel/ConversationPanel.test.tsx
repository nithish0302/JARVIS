import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ConversationPanel } from "./ConversationPanel";
import { useAppStore } from "../../../stores/useAppStore";

vi.mock("../../../services/jarvisApi", () => ({
  getConversations: vi.fn().mockResolvedValue([
    { id: "c1", title: "Rust ownership notes", preview: "borrow checker", updated_at: new Date().toISOString() },
    { id: "c2", title: "Grocery list", preview: "milk and eggs", updated_at: new Date().toISOString() },
  ]),
  getConversation: vi.fn().mockResolvedValue([]),
  updateConversationTitle: vi.fn().mockResolvedValue({}),
  deleteConversation: vi.fn().mockResolvedValue({}),
  verifyDeletePin: vi.fn().mockResolvedValue(true),
}));

describe("ConversationPanel search", () => {
  beforeEach(() => {
    useAppStore.setState({
      conversationPanelOpen: true,
      deletingConversationId: null,
      conversationSearchFocusToken: 0,
    });
  });

  it("lists all conversations with an empty filter", async () => {
    render(<ConversationPanel />);
    expect(await screen.findByText("Rust ownership notes")).toBeInTheDocument();
    expect(screen.getByText("Grocery list")).toBeInTheDocument();
  });

  it("filters by title", async () => {
    render(<ConversationPanel />);
    await screen.findByText("Rust ownership notes");
    fireEvent.change(screen.getByLabelText("Filter conversations"), {
      target: { value: "grocery" },
    });
    await waitFor(() => {
      expect(screen.queryByText("Rust ownership notes")).toBeNull();
    });
    expect(screen.getByText("Grocery list")).toBeInTheDocument();
  });

  it("filters by preview text too", async () => {
    render(<ConversationPanel />);
    await screen.findByText("Rust ownership notes");
    fireEvent.change(screen.getByLabelText("Filter conversations"), {
      target: { value: "borrow" },
    });
    await waitFor(() => {
      expect(screen.queryByText("Grocery list")).toBeNull();
    });
    expect(screen.getByText("Rust ownership notes")).toBeInTheDocument();
  });

  it("is case-insensitive", async () => {
    render(<ConversationPanel />);
    await screen.findByText("Rust ownership notes");
    fireEvent.change(screen.getByLabelText("Filter conversations"), {
      target: { value: "RUST" },
    });
    await waitFor(() => {
      expect(screen.queryByText("Grocery list")).toBeNull();
    });
    expect(screen.getByText("Rust ownership notes")).toBeInTheDocument();
  });

  it("shows a distinct empty state when the filter matches nothing", async () => {
    render(<ConversationPanel />);
    await screen.findByText("Rust ownership notes");
    fireEvent.change(screen.getByLabelText("Filter conversations"), {
      target: { value: "zzzz" },
    });
    await waitFor(() => {
      expect(screen.getByText(/No conversations match/)).toBeInTheDocument();
    });
  });

  it("focuses the search input when Ctrl+F requests it", async () => {
    render(<ConversationPanel />);
    await screen.findByText("Rust ownership notes");
    const input = screen.getByLabelText("Filter conversations");
    expect(document.activeElement).not.toBe(input);
    useAppStore.getState().requestConversationSearchFocus();
    await waitFor(() => {
      expect(document.activeElement).toBe(input);
    });
  });
});
