import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Button } from "./Button";

test("disables and announces a loading button", () => {
  render(<Button loading>Save</Button>);

  const button = screen.getByRole("button", { name: /saveloading/i });
  expect(button).toBeDisabled();
  expect(button).toHaveAttribute("aria-busy", "true");
});
