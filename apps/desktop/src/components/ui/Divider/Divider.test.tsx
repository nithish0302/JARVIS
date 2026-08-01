import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Divider } from "./Divider";

test("uses separator semantics for vertical dividers", () => {
  render(<Divider orientation="vertical" />);

  expect(screen.getByRole("separator")).toHaveAttribute("aria-orientation", "vertical");
});
