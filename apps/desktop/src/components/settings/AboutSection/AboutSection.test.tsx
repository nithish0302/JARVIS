import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AboutSection } from "./AboutSection";

describe("AboutSection", () => {
  it("renders about details", () => {
    render(<AboutSection />);

    expect(screen.getByText("JARVIS")).toBeInTheDocument();
    expect(screen.getByText("0.1.0")).toBeInTheDocument();
    expect(screen.getByText("Nithish")).toBeInTheDocument();
  });
});
