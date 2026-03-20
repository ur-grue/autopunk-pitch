import { InputHTMLAttributes, SelectHTMLAttributes, LabelHTMLAttributes } from "react";

export function Input({
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`mt-1 block w-full rounded bg-transparent ghost-border px-3 py-2 text-sm text-on-surface font-body placeholder:text-outline focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/30 transition-colors ${className}`}
      {...props}
    />
  );
}

export function Select({
  className = "",
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`mt-1 block w-full rounded bg-surface ghost-border px-3 py-2 text-sm text-on-surface font-body focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/30 transition-colors ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}

export function Label({
  className = "",
  children,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={`label-uppercase text-outline block ${className}`}
      {...props}
    >
      {children}
    </label>
  );
}
