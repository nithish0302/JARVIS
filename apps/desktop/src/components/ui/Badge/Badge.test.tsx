import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Badge } from "./Badge";

test("renders descriptive status text", () => {
  render(<Badge tone="success">Connected</Badge>);

  expect(screen.getByText("Connected")).toBeInTheDocument();
});
