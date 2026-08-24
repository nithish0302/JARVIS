import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { LeftColumn } from "./LeftColumn";
import { useMicLevelStore } from "../../../stores/useMicLevelStore";

// Real RMS mic levels from the backend run well under 1.0 for normal room
// tone and speech (see core/config.py: silence_threshold=0.01,
// TTS_INTERRUPT_LEVEL_THRESHOLD=0.18), so a bar that renders scaleY(rawLevel)
// directly is visually indistinguishable from zero across that whole
// realistic range - it "reacts" in the DOM but reads as a flat line on
// screen. These tests pin the gain applied on top of the raw level so a
// realistic RMS value produces a visibly non-flat bar.
//
// The store still keeps 40 raw samples of history; the panel groups them
// into WAVEFORM_BAR_COUNT (20) averaged bars for display density, so tests
// that check per-sample variation set values in blocks that span a whole
// group rather than alternating every single history index.
describe("LeftColumn mic waveform", () => {
  beforeEach(() => {
    useMicLevelStore.setState({ level: 0, history: [] });
  });

  const bars = (container: HTMLElement) =>
    Array.from(container.querySelectorAll(".mic-waveform-bars span")) as HTMLElement[];

  const scaleYOf = (el: HTMLElement) => {
    const match = el.style.transform.match(/scaleY\(([\d.]+)\)/);
    return match ? Number(match[1]) : NaN;
  };

  it("renders a reduced, clean bar count (20) instead of 40 raw samples", () => {
    useMicLevelStore.setState({ history: Array(40).fill(0.05) });
    const { container } = render(<LeftColumn />);
    expect(bars(container).length).toBe(20);
  });

  it("renders a visibly non-flat bar for a realistic quiet-speech RMS level", () => {
    useMicLevelStore.setState({ history: Array(40).fill(0.05) });
    const { container } = render(<LeftColumn />);
    const heights = bars(container).map(scaleYOf);
    // 0.05 raw RMS must not collapse to the near-invisible floor - it should
    // read as a clearly taller bar than true silence.
    expect(heights[0]).toBeGreaterThan(0.15);
  });

  it("bar height varies across groups as the underlying history varies", () => {
    // First half of the buffer quiet, second half loud - spans full groups
    // rather than alternating within a group (which would average out).
    const history = [...Array(20).fill(0.02), ...Array(20).fill(0.2)];
    useMicLevelStore.setState({ history });
    const { container } = render(<LeftColumn />);
    const heights = bars(container).map(scaleYOf);
    expect(heights[heights.length - 1]).toBeGreaterThan(heights[0]);
    expect(heights[0]).not.toBeCloseTo(heights[heights.length - 1], 2);
  });

  it("falls back to a low but non-zero baseline in silence", () => {
    useMicLevelStore.setState({ history: Array(40).fill(0) });
    const { container } = render(<LeftColumn />);
    const heights = bars(container).map(scaleYOf);
    expect(heights[0]).toBeGreaterThan(0);
    expect(heights[0]).toBeLessThan(0.15);
  });

  it("re-renders with new bar heights as the store's history updates", () => {
    const { container, rerender } = render(<LeftColumn />);
    const quiet = bars(container).map(scaleYOf);

    useMicLevelStore.setState({ history: Array(40).fill(0.3) });
    rerender(<LeftColumn />);
    const loud = bars(container).map(scaleYOf);

    expect(loud[0]).toBeGreaterThan(quiet[0]);
  });
});
