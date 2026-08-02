import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SendButton } from "./SendButton";

describe("SendButton", () => {
  it("renders a send button and responds to clicks", async () => {
    const onClick = vi.fn();
    render(<SendButton onClick={onClick} />);

    const button = screen.getByRole("button", { name: "Send message" });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();

    await userEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when the disabled prop is true", () => {
    const onClick = vi.fn();
    render(<SendButton disabled onClick={onClick} />);

    const button = screen.getByRole("button", { name: "Send message" });
    expect(button).toBeDisabled();
  });
});
