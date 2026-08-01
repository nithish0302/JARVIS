import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Switch } from "./Switch";

test("renders a labeled switch", () => {
  render(<Switch label="Voice activation" />);

  expect(screen.getByRole("switch", { name: "Voice activation" })).toBeInTheDocument();
});
