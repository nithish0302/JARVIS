import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Textarea } from "./Textarea";

test("associates its label, description, and error with the control", () => {
  render(<Textarea description="Add details" error="Instructions are required" label="Instructions" />);

  const textarea = screen.getByRole("textbox", { name: "Instructions" });
  expect(textarea).toHaveAttribute("aria-invalid", "true");
  expect(textarea).toHaveAttribute("aria-describedby", expect.stringContaining("-description"));
  expect(textarea).toHaveAttribute("aria-describedby", expect.stringContaining("-error"));
  expect(screen.getByRole("alert")).toHaveTextContent("Instructions are required");
});
