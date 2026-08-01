import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { IconButton } from "./IconButton";

test("uses its required accessible label", () => {
  render(<IconButton aria-label="Close">×</IconButton>);

  expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
});
