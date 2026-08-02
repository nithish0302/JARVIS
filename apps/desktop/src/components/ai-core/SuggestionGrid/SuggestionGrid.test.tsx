import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SuggestionGrid } from "./SuggestionGrid";

describe("SuggestionGrid", () => {
  it("renders a grid of four suggestion cards", () => {
    render(<SuggestionGrid />);
    expect(screen.getByText("Ask a question")).toBeInTheDocument();
    expect(screen.getByText("Write some code")).toBeInTheDocument();
    expect(screen.getByText("Summarize a document")).toBeInTheDocument();
    expect(screen.getByText("Analyze data")).toBeInTheDocument();
  });
});
