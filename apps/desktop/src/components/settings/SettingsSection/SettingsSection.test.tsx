import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SettingsSection } from "./SettingsSection";

describe("SettingsSection", () => {
  it("renders title, description, and children", () => {
    render(
      <SettingsSection title="Test Title" description="Test Description">
        <div>Child Content</div>
      </SettingsSection>
    );

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test Description")).toBeInTheDocument();
    expect(screen.getByText("Child Content")).toBeInTheDocument();
  });
});
