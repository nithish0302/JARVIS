import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PersonalitySection } from "./PersonalitySection";

describe("PersonalitySection", () => {
  it("renders personality, address, briefing, and PIN controls", () => {
    render(<PersonalitySection />);

    expect(screen.getByText("Personality")).toBeInTheDocument();
    expect(screen.getByLabelText("Personality Mode")).toBeInTheDocument();
    expect(screen.getByLabelText("Response Modifier")).toBeInTheDocument();
    expect(screen.getByLabelText("Address as")).toBeInTheDocument();
    expect(screen.getByLabelText("Daily Briefing")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByLabelText("New PIN")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm PIN")).toBeInTheDocument();

    // Provider/model settings now live in AIProviderSection, not here.
    expect(screen.queryByLabelText("Provider")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Model name")).not.toBeInTheDocument();
  });
});
