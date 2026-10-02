import type {
  InputHTMLAttributes,
  LabelHTMLAttributes,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cx } from "@/lib/styles";

const control =
  "w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3.5 py-2.5 text-sm text-white placeholder:text-slate-600 transition hover:border-[var(--stroke-strong)] focus:border-teal-300 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50";

export function FieldLabel({
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cx("mb-2 block text-sm font-medium text-slate-300", className)}
      {...props}
    />
  );
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cx(control, className)} {...props} />;
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cx(control, className)} {...props} />;
}

export function Textarea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cx(control, "resize-y", className)} {...props} />;
}
