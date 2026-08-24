import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SettingsView } from "./SettingsView";

describe("SettingsView", () => {
  it("renders AI Provider by default", () => {
    render(<SettingsView />);
    expect(
      screen.getByText("Configure the AI engine provider, model, and API credentials.")
    ).toBeInTheDocument();
  });

  it("navigates to the Personality tab and shows its content", async () => {
    const user = userEvent.setup();
    render(<SettingsView />);

    await user.click(screen.getByText("Personality"));

    expect(
      screen.getByText("Configure how JARVIS behaves, addresses you, and protects your conversations.")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Personality Mode")).toBeInTheDocument();
    expect(screen.getByLabelText("New PIN")).toBeInTheDocument();
    // Switching tabs, not staying on AI Provider's content.
    expect(screen.queryByLabelText("Provider")).not.toBeInTheDocument();
  });
});
