import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Field } from "./Field";

test("connects its label and exposes errors", () => {
  render(
    <Field error="Name is required" errorId="name-error" htmlFor="name" label="Name" required>
      <input aria-describedby="name-error" id="name" />
    </Field>,
  );

  expect(screen.getByRole("textbox", { name: /name/i })).toBeInTheDocument();
  expect(screen.getByRole("alert")).toHaveTextContent("Name is required");
});
