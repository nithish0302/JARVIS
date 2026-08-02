import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ComposerToolbar } from "./ComposerToolbar";

describe("ComposerToolbar", () => {
  it("renders the empty placeholder toolbar", () => {
    const { container } = render(<ComposerToolbar />);
    // Currently renders an empty div, so we just check it doesn't crash
    expect(container.firstChild).toBeInTheDocument();
  });
});
