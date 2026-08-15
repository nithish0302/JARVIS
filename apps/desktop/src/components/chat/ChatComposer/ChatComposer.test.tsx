import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ChatComposer } from "./ChatComposer";

describe("ChatComposer", () => {
  it("renders the textarea and updates on typing", async () => {
    render(<ChatComposer onSend={vi.fn()} />);
    const textarea = screen.getByRole("textbox", { name: "Message" });
    
    await userEvent.type(textarea, "Hello JARVIS");
    expect(textarea).toHaveValue("Hello JARVIS");
  });

  it("calls onSend and clears input when pressing Enter", async () => {
    const onSend = vi.fn();
    render(<ChatComposer onSend={onSend} />);
    const textarea = screen.getByRole("textbox", { name: "Message" });

    await userEvent.type(textarea, "Execute command{Enter}");
    expect(onSend).toHaveBeenCalledWith("Execute command");
    expect(textarea).toHaveValue("");
  });

  it("inserts newline on Shift+Enter instead of sending", async () => {
    const onSend = vi.fn();
    render(<ChatComposer onSend={onSend} />);
    const textarea = screen.getByRole("textbox", { name: "Message" });

    await userEvent.type(textarea, "Line 1{Shift>}{Enter}{/Shift}Line 2");
    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("Line 1\nLine 2");
  });

  it("shows character count when exceeding 500 characters", async () => {
    render(<ChatComposer onSend={vi.fn()} />);
    const textarea = screen.getByRole("textbox", { name: "Message" });

    const longText = "a".repeat(501);
    fireEvent.change(textarea, { target: { value: longText } });

    const count = await screen.findByText("501 / 500");
    expect(count).toBeInTheDocument();
  });
});
