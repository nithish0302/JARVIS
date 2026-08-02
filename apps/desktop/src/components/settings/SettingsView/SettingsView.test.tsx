import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SettingsView } from "./SettingsView";

describe("SettingsView", () => {
  it("renders AI Provider by default", () => {
    render(<SettingsView />);
    expect(screen.getByText("Configure the AI engine that powers JARVIS.")).toBeInTheDocument();
  });
});
