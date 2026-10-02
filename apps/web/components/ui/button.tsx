import type { ButtonHTMLAttributes } from "react";

import { cx } from "@/lib/styles";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-teal-300 text-slate-950 shadow-lg shadow-teal-950/20 hover:bg-teal-200",
  secondary:
    "border border-[var(--stroke)] bg-[var(--surface)] text-white hover:border-[var(--stroke-strong)] hover:bg-[var(--surface-hover)]",
  ghost: "text-slate-300 hover:bg-white/5 hover:text-white",
  danger: "border border-rose-400/20 bg-rose-400/10 text-rose-100 hover:bg-rose-400/15",
};

const sizes: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3 py-2 text-sm",
  md: "min-h-11 px-4 py-2.5 text-sm",
  lg: "min-h-12 px-5 py-3 text-base",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  size?: ButtonSize;
  variant?: ButtonVariant;
};

export function Button({
  className,
  size = "md",
  type = "button",
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition duration-200",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-300",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      type={type}
      {...props}
    />
  );
}
