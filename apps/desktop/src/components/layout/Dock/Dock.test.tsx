import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Dock } from "./Dock";

describe("Dock", () => {
  it("has no mic indicator - the waveform lives in the Inspector column now", () => {
    const { container } = render(<Dock />);
    const buttons = container.querySelectorAll("button");
    expect(buttons.length).toBe(3);
    expect(container.querySelector(".dock-mic")).toBeNull();
    expect(container.querySelector(".dock-mic-wrap")).toBeNull();
    expect(container.querySelector(".dock-mic-ring")).toBeNull();
    expect(container.querySelector(".dock-mic-meter")).toBeNull();
  });
});
