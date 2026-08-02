import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppearanceSection } from "./AppearanceSection";

describe("AppearanceSection", () => {
  it("renders a disabled dark mode switch", () => {
    render(<AppearanceSection />);

    expect(screen.getByText("Appearance")).toBeInTheDocument();
    const switchControl = screen.getByLabelText("Dark Mode");
    expect(switchControl).toBeInTheDocument();
    expect(switchControl).toBeDisabled();
    expect(screen.getByText("Additional themes coming soon")).toBeInTheDocument();
  });
});
