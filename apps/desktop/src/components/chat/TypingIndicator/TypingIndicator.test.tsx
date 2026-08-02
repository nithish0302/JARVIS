import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TypingIndicator } from "./TypingIndicator";

describe("TypingIndicator", () => {
  it("does not render when visible is false", () => {
    const { container } = render(<TypingIndicator visible={false} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the typing indicator when visible is true", () => {
    render(<TypingIndicator visible={true} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Assistant is typing");
  });
});
