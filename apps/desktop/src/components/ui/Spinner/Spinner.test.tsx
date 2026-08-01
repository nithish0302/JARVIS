import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Spinner } from "./Spinner";

test("announces its loading label", () => {
  render(<Spinner label="Loading conversation" />);

  expect(screen.getByRole("status", { name: "Loading conversation" })).toBeInTheDocument();
});
