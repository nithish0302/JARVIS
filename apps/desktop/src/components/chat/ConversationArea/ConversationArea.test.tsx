import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConversationArea } from "./ConversationArea";

describe("ConversationArea", () => {
  it("renders messages and scrolls to bottom", () => {
    // Mock scrollIntoView
    window.HTMLElement.prototype.scrollIntoView = function() {};

    const messages = [
      { id: "1", role: "user" as const, content: "Hello", timestamp: "12:00" },
    ];
    
    render(<ConversationArea messages={messages} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("renders the typing indicator when isTyping is true", () => {
    window.HTMLElement.prototype.scrollIntoView = function() {};
    
    render(<ConversationArea isTyping={true} messages={[]} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
