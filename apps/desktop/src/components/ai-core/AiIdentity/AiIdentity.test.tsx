import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AiIdentity } from "./AiIdentity";

describe("AiIdentity", () => {
  it("renders the JARVIS heading and subtitle", () => {
    render(<AiIdentity />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("JARVIS");
    expect(screen.getByText("Personal AI Assistant")).toBeInTheDocument();
  });
});
