import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageAvatar } from "./MessageAvatar";

describe("MessageAvatar", () => {
  it("renders a user initial for the user role", () => {
    render(<MessageAvatar role="user" />);
    expect(screen.getByText("U")).toBeInTheDocument();
  });

  it("renders an avatar for the assistant role", () => {
    const { container } = render(<MessageAvatar role="assistant" />);
    // The assistant avatar does not contain the "U" text.
    expect(screen.queryByText("U")).not.toBeInTheDocument();
    // Verify it renders the glow div
    expect(container.querySelector(".bg-\\[var\\(--color-highlight\\)\\]")).toBeInTheDocument();
  });
});
