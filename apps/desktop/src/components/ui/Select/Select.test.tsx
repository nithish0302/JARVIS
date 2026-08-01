import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Select } from "./Select";

test("renders a labeled native select", () => {
  render(
    <Select label="Mode">
      <option value="automatic">Automatic</option>
    </Select>,
  );

  expect(screen.getByRole("combobox", { name: "Mode" })).toBeInTheDocument();
});
