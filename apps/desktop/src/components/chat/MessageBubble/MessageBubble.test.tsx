import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageBubble } from "./MessageBubble";

describe("MessageBubble", () => {
  it("renders a user message correctly", () => {
    const { container } = render(
      <MessageBubble content="Hello JARVIS" role="user" timestamp="12:00 PM" />
    );
    expect(screen.getByText("Hello JARVIS")).toBeInTheDocument();
    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.getByText("12:00 PM")).toBeInTheDocument();
    
    // Check if it has flex-row-reverse for user
    expect(container.firstChild).toHaveClass("flex-row-reverse");
  });

  it("renders an assistant message correctly", () => {
    const { container } = render(
      <MessageBubble content="Hello Sir" role="assistant" timestamp="12:01 PM" />
    );
    expect(screen.getByText("Hello Sir")).toBeInTheDocument();
    expect(screen.getByText("JARVIS")).toBeInTheDocument();
    
    // Check if it has flex-row for assistant
    expect(container.firstChild).toHaveClass("flex-row");
  });
});
