import { ReactNode } from "react";

export function Card({
  children,
  className = "",
  hover = true,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`bg-surface-container rounded-lg p-6 ghost-border ${
        hover ? "hover:bg-surface-container-high transition-all duration-200" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}
