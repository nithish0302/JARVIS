import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ActionFeedback } from "./ActionFeedback";
import { useAppStore } from "../../../stores/useAppStore";

describe("ActionFeedback", () => {
  beforeEach(() => {
    useAppStore.setState({ actionFeedback: "", actionFeedbackVisible: false });
    vi.useFakeTimers();
  });

  it("does not render when invisible", () => {
    useAppStore.setState({ actionFeedback: "Test message", actionFeedbackVisible: false });
    render(<ActionFeedback />);
    expect(screen.queryByText("Test message")).not.toBeInTheDocument();
  });

  it("renders when visible and message exists", () => {
    useAppStore.setState({ actionFeedback: "Test message", actionFeedbackVisible: true });
    render(<ActionFeedback />);
    expect(screen.getByText("Test message")).toBeInTheDocument();
  });
});
