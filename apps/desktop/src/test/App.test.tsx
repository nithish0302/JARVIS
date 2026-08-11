import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import App from "../App";

test("renders the application HUD layout", () => {
  const { container } = render(<App />);
  expect(container.querySelector(".stage")).toBeInTheDocument();
  expect(container.querySelector(".dock")).toBeInTheDocument();
  expect(screen.getByText("J.A.R.V.I.S")).toBeInTheDocument();
});
