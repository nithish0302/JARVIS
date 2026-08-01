export function OverlayLayer() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-[var(--z-overlay)]"
      data-layout-overlay=""
    />
  );
}
