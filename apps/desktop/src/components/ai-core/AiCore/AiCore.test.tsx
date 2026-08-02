import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AiCore } from "./AiCore";

describe("AiCore", () => {
  it("renders the idle state by default", () => {
    const { container } = render(<AiCore />);
    expect(container.firstChild).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector(".bg-\\[var\\(--color-highlight\\)\\]")).toBeInTheDocument();
  });

  it("applies custom class names", () => {
    const { container } = render(<AiCore className="custom-class" />);
    expect(container.firstChild).toHaveClass("custom-class");
  });
});
