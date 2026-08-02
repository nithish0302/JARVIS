import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SettingsSidebar } from "./SettingsSidebar";

describe("SettingsSidebar", () => {
  it("renders navigation items", () => {
    render(
      <SettingsSidebar activeSection="ai-provider" onSectionSelect={() => {}} />
    );

    expect(screen.getByText("AI Provider")).toBeInTheDocument();
    expect(screen.getByText("Appearance")).toBeInTheDocument();
    expect(screen.getByText("About")).toBeInTheDocument();
  });

  it("calls onSectionSelect when an item is clicked", async () => {
    const onSectionSelect = vi.fn();
    const user = userEvent.setup();

    render(
      <SettingsSidebar
        activeSection="ai-provider"
        onSectionSelect={onSectionSelect}
      />
    );

    await user.click(screen.getByText("Appearance"));
    expect(onSectionSelect).toHaveBeenCalledWith("appearance");
  });
});
