import { ButtonHTMLAttributes } from "react";

export function Button({
  className = "",
  disabled,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`btn-gradient font-display px-6 py-3 text-xs font-bold uppercase tracking-[0.15em] rounded hover:shadow-glow active:scale-[0.98] transition-all duration-200 ${
        disabled ? "opacity-40 pointer-events-none" : ""
      } ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
