import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Panel } from "./Panel";

test("renders a semantic section", () => {
  render(<Panel aria-label="Activity">Recent activity</Panel>);

  expect(screen.getByRole("region", { name: "Activity" })).toHaveTextContent("Recent activity");
});
