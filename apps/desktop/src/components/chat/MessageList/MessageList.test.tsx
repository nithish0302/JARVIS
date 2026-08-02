import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageList } from "./MessageList";

describe("MessageList", () => {
  it("renders nothing when messages are empty", () => {
    const { container } = render(<MessageList messages={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a list of messages", () => {
    const messages = [
      { id: "1", role: "user" as const, content: "Hello", timestamp: "12:00" },
      { id: "2", role: "assistant" as const, content: "Hi", timestamp: "12:01" },
    ];
    render(<MessageList messages={messages} />);
    
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi")).toBeInTheDocument();
    expect(screen.getByRole("log")).toBeInTheDocument();
  });
});
