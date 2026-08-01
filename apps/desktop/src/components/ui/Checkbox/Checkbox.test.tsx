import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Checkbox } from "./Checkbox";

test("renders a labeled native checkbox", () => {
  render(<Checkbox label="Enable notifications" />);

  expect(screen.getByRole("checkbox", { name: "Enable notifications" })).toBeInTheDocument();
});
