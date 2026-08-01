import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Skeleton } from "./Skeleton";

test("is hidden from assistive technology", () => {
  const { container } = render(<Skeleton variant="circle" />);

  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(container.firstChild).toHaveAttribute("aria-hidden", "true");
});
