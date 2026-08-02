import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AiCoreIdle } from "./AiCoreIdle";

describe("AiCoreIdle", () => {
  it("renders without crashing", () => {
    const { container } = render(<AiCoreIdle />);
    expect(container.firstChild).toBeInTheDocument();
  });
});
