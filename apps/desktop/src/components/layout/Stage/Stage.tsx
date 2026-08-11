import { ReactNode } from "react";
import { cn } from "../../../lib/cn";
import "./Stage.css";

interface Props {
  children: ReactNode;
  className?: string;
}

export function Stage({ children }: Props) {
  return <div className="stage">{children}</div>;
}

export function Scene({ children, className }: Props) {
  return <div className={cn("scene", className)}>{children}</div>;
}
