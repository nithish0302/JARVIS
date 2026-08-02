import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SuggestionCard } from "./SuggestionCard";

describe("SuggestionCard", () => {
  it("renders the label text", () => {
    render(<SuggestionCard label="Test label" />);
    expect(screen.getByText("Test label")).toBeInTheDocument();
  });
});
