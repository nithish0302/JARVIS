import type { ReactNode } from "react";

export interface LayoutProviderProps {
  children: ReactNode;
}

export function LayoutProvider({ children }: LayoutProviderProps) {
  return (
    <div className="h-full" data-theme="dark">
      {children}
    </div>
  );
}
