import type { HTMLAttributes, TableHTMLAttributes } from "react";

import { cx } from "@/lib/styles";

export function TableFrame({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cx(
        "overflow-x-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)]",
        className,
      )}
      {...props}
    />
  );
}

export function Table({ className, ...props }: TableHTMLAttributes<HTMLTableElement>) {
  return (
    <table
      className={cx(
        "w-full min-w-[640px] text-left text-sm [&_tbody_tr]:border-t [&_tbody_tr]:border-[var(--stroke)]",
        "[&_tbody_tr]:transition [&_tbody_tr:hover]:bg-white/[0.025] [&_td]:px-4 [&_td]:py-3.5",
        "[&_th]:bg-white/[0.025] [&_th]:px-4 [&_th]:py-3 [&_th]:text-xs [&_th]:font-semibold",
        "[&_th]:uppercase [&_th]:tracking-[0.08em] [&_th]:text-slate-500",
        className,
      )}
      {...props}
    />
  );
}
