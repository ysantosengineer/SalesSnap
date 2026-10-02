import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cx } from "@/lib/styles";

type FeedbackTone = "info" | "success" | "warning" | "danger";

const tones: Record<FeedbackTone, string> = {
  info: "border-indigo-300/20 bg-indigo-300/8 text-indigo-100",
  success: "border-emerald-300/20 bg-emerald-300/8 text-emerald-100",
  warning: "border-amber-300/20 bg-amber-300/8 text-amber-100",
  danger: "border-rose-300/20 bg-rose-300/8 text-rose-100",
};

export function Alert({
  children,
  className,
  tone = "info",
}: {
  children: ReactNode;
  className?: string;
  tone?: FeedbackTone;
}) {
  return (
    <div className={cx("rounded-xl border px-4 py-3 text-sm leading-6", tones[tone], className)}>
      {children}
    </div>
  );
}

export function LoadingState({ label = "Loading your workspace..." }: { label?: string }) {
  return (
    <div className="flex min-h-56 items-center justify-center gap-3 text-sm text-slate-400" role="status">
      <span
        aria-hidden="true"
        className="h-5 w-5 animate-spin rounded-full border-2 border-slate-700 border-t-teal-300"
      />
      {label}
    </div>
  );
}

export function EmptyState({
  actionHref,
  actionLabel,
  description,
  title,
}: {
  actionHref?: string;
  actionLabel?: string;
  description: string;
  title: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-[var(--stroke-strong)] bg-white/[0.02] px-6 py-12 text-center">
      <div className="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-teal-300/10 text-xl text-teal-200">
        ◇
      </div>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">{description}</p>
      {actionHref && actionLabel && (
        <Link
          className="mt-5 inline-flex rounded-xl bg-teal-300 px-4 py-2.5 text-sm font-semibold text-slate-950"
          href={actionHref}
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <Alert tone="danger">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-semibold">We couldn’t load this view</p>
          <p className="mt-0.5 text-rose-200/80">{message}</p>
        </div>
        {onRetry && (
          <Button onClick={onRetry} size="sm" variant="danger">
            Try again
          </Button>
        )}
      </div>
    </Alert>
  );
}
