import type { ReactNode } from "react";

export interface SettingsLayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

export function SettingsLayout({ sidebar, children }: SettingsLayoutProps) {
  return (
    // h-full + min-h-0 let this fill SettingsView's bounded h-full instead
    // of sizing to content: a lone child in a column flex container does
    // NOT auto-stretch along the main axis, so without h-full here this box
    // (and everything inside it) grows as tall as its content demands,
    // pushing the page past the viewport with nothing left to scroll
    // against. min-h-0 overrides the flex-item default min-height:auto,
    // which otherwise refuses to let this shrink below its content size -
    // that's what actually lets the overflow-y-auto content pane below
    // engage instead of silently being clipped.
    <div className="mx-auto flex h-full min-h-0 w-full max-w-5xl gap-[var(--space-8)] p-[var(--space-8)]">
      <aside className="shrink-0">{sidebar}</aside>
      <div className="flex-1 min-h-0 min-w-0">{children}</div>
    </div>
  );
}
