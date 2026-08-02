import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WelcomeMessage } from "./WelcomeMessage";

describe("WelcomeMessage", () => {
  it("renders the greeting and question", () => {
    render(<WelcomeMessage />);
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("Hello.");
    expect(screen.getByText("How can I help you today?")).toBeInTheDocument();
  });
});
