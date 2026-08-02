import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { IdleView } from "./IdleView";

describe("IdleView", () => {
  it("renders the AI Core, Identity, WelcomeMessage, and SuggestionGrid", () => {
    render(<IdleView />);
    
    // Check AiIdentity
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("JARVIS");
    
    // Check WelcomeMessage
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("Hello.");
    
    // Check SuggestionGrid
    expect(screen.getByText("Ask a question")).toBeInTheDocument();
  });
});
