"use client";

import { useEffect, type ReactNode } from "react";

import { Button } from "@/components/ui/button";

export function Modal({
  children,
  confirmLabel = "Confirm",
  description,
  onClose,
  onConfirm,
  open,
  title,
}: {
  children?: ReactNode;
  confirmLabel?: string;
  description?: string;
  onClose: () => void;
  onConfirm?: () => void;
  open: boolean;
  title: string;
}) {
  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose, open]);

  if (!open) return null;

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-[100] grid place-items-center bg-slate-950/80 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) onClose();
      }}
      role="dialog"
    >
      <section className="w-full max-w-md rounded-2xl border border-[var(--stroke)] bg-[var(--surface-raised)] p-6 shadow-2xl">
        <h2 className="text-xl font-semibold">{title}</h2>
        {description && <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>}
        {children}
        <div className="mt-6 flex justify-end gap-3">
          <Button onClick={onClose} variant="ghost">
            Cancel
          </Button>
          {onConfirm && <Button onClick={onConfirm}>{confirmLabel}</Button>}
        </div>
      </section>
    </div>
  );
}
