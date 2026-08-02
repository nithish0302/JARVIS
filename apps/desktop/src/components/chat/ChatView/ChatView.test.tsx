import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ChatView } from "./ChatView";

describe("ChatView", () => {
  it("renders the ConversationArea and ChatComposer", () => {
    window.HTMLElement.prototype.scrollIntoView = function() {};
    render(<ChatView />);
    
    expect(screen.getByText("Initialize system diagnostics.")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Message" })).toBeInTheDocument();
  });

  it("adds a new message when sending from ChatComposer", async () => {
    window.HTMLElement.prototype.scrollIntoView = function() {};
    render(<ChatView />);

    const textarea = screen.getByRole("textbox", { name: "Message" });
    await userEvent.type(textarea, "Testing new message{Enter}");

    expect(screen.getByText("Testing new message")).toBeInTheDocument();
  });
});
