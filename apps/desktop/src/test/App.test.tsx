import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import App from "../App";

test("renders the application shell landmarks", () => {
  render(<App />);
  expect(screen.getByRole("banner", { name: "Application header" })).toBeInTheDocument();
  expect(screen.getByRole("main")).toBeInTheDocument();
});
