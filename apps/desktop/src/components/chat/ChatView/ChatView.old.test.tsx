import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { ChatView } from "./ChatView.old";
import { useConversationStore } from "../../../stores/useConversationStore";

describe("ChatView", () => {
  beforeEach(() => {
    useConversationStore.getState().clearConversation();
  });

  it("renders the IdleView and ChatComposer by default", () => {
    window.HTMLElement.prototype.scrollIntoView = function() {};
    render(<ChatView />);
    
    expect(screen.getByText("JARVIS")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Message" })).toBeInTheDocument();
  });

  it("adds a new message when sending from ChatComposer", async () => {
    window.HTMLElement.prototype.scrollIntoView = function() {};
    render(<ChatView />);

    const textarea = screen.getByRole("textbox", { name: "Message" });
    await userEvent.type(textarea, "Testing new message{Enter}");

    await waitFor(() => {
      expect(screen.getByText("Testing new message")).toBeInTheDocument();
    });
  });
});
