import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { StatusIndicator } from "./StatusIndicator";

test("announces a polite status when requested", () => {
  render(<StatusIndicator label="Connected" live="polite" tone="success" />);

  expect(screen.getByRole("status")).toHaveTextContent("Connected");
  expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
});
