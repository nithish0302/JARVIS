import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Input } from "./Input";

test("associates its label, description, and error with the control", () => {
  render(<Input description="A unique project label" error="Name is required" label="Name" />);

  const input = screen.getByLabelText("Name");
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAttribute("aria-describedby", expect.stringContaining("-description"));
  expect(input).toHaveAttribute("aria-describedby", expect.stringContaining("-error"));
  expect(screen.getByRole("alert")).toHaveTextContent("Name is required");
});
