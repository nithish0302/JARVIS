import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AIProviderSection } from "./AIProviderSection";

describe("AIProviderSection", () => {
  it("renders select and input", () => {
    render(<AIProviderSection />);

    expect(screen.getByText("AI Provider")).toBeInTheDocument();
    expect(screen.getByLabelText("Provider")).toBeInTheDocument();
    expect(screen.getByLabelText("Model name")).toBeInTheDocument();
  });
});
