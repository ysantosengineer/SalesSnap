"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { useAuth } from "@/components/auth-provider";
import { Brand } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { cx } from "@/lib/styles";

type IconName =
  | "alert"
  | "box"
  | "chart"
  | "chat"
  | "dashboard"
  | "forecast"
  | "import"
  | "inventory"
  | "segments";

const navigation = [
  {
    label: "Overview",
    items: [{ label: "Dashboard", href: "/dashboard", icon: "dashboard" }],
  },
  {
    label: "Data",
    items: [
      { label: "Import sales", href: "/import", icon: "import" },
      { label: "Inventory", href: "/inventory", icon: "inventory" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { label: "Customer segments", href: "/customers/segments", icon: "segments" },
      { label: "Demand forecast", href: "/forecast", icon: "forecast" },
      { label: "Anomalies", href: "/anomalies", icon: "alert" },
      { label: "Stock risk", href: "/stock-risk", icon: "box" },
    ],
  },
  {
    label: "AI workspace",
    items: [
      { label: "AI insights", href: "/insights", icon: "chart" },
      { label: "AI chat", href: "/chat", icon: "chat" },
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  items: ReadonlyArray<{ label: string; href: string; icon: IconName }>;
}>;

const publicPaths = new Set(["/", "/login", "/register"]);

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, ReactNode> = {
    alert: <path d="M12 9v4m0 4h.01M10.3 3.7 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z" />,
    box: <path d="m4 7 8-4 8 4-8 4-8-4Zm0 0v10l8 4 8-4V7m-8 4v10" />,
    chart: <path d="M4 19V9m6 10V5m6 14v-7m4 7H2" />,
    chat: <path d="M7 18.5 3.5 21v-5A8.5 8.5 0 1 1 7 18.5ZM8 10h8m-8 4h5" />,
    dashboard: <path d="M4 4h6v6H4V4Zm10 0h6v10h-6V4ZM4 14h6v6H4v-6Zm10 4h6v2h-6v-2Z" />,
    forecast: <path d="M3 18 8 13l4 3 8-10m-5 0h5v5" />,
    import: <path d="M12 3v12m-4-4 4 4 4-4M5 19h14" />,
    inventory: <path d="M4 5h16v4H4V5Zm1 4v11h14V9M9 13h6" />,
    segments: <path d="M8 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8 2a3 3 0 1 0 0-6m-8 7c-3.3 0-6 2-6 4.5V21h12v-2.5C14 16 11.3 14 8 14Zm8 1c2.8 0 5 1.6 5 3.5V21h-4" />,
  };

  return (
    <svg
      aria-hidden="true"
      className="h-5 w-5 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.7"
      viewBox="0 0 24 24"
    >
      {paths[name]}
    </svg>
  );
}

function NavigationContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav aria-label="SalesSnap modules" className="flex-1 overflow-y-auto px-3 py-5">
      {navigation.map((group) => (
        <div className="mb-6" key={group.label}>
          <p className="mb-2 px-3 text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-600">
            {group.label}
          </p>
          <div className="space-y-1">
            {group.items.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  aria-current={active ? "page" : undefined}
                  className={cx(
                    "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition",
                    active
                      ? "bg-teal-300/10 text-teal-200 shadow-[inset_0_0_0_1px_rgba(94,234,212,0.12)]"
                      : "text-slate-400 hover:bg-white/[0.04] hover:text-white",
                  )}
                  href={item.href}
                  key={item.href}
                  onClick={onNavigate}
                >
                  <Icon name={item.icon} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isLoading, logout, user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);

  if (publicPaths.has(pathname) || isLoading || !user) return children;

  const initials = user.email.slice(0, 2).toUpperCase();

  async function handleLogout() {
    await logout();
    setLogoutOpen(false);
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-[var(--canvas)] text-white">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-[var(--stroke)] bg-[var(--surface)] lg:flex lg:flex-col">
        <div className="border-b border-[var(--stroke)] px-5 py-5">
          <Brand compact href="/dashboard" />
        </div>
        <NavigationContent />
        <div className="border-t border-[var(--stroke)] p-4">
          <button
            className="flex w-full items-center gap-3 rounded-xl p-2 text-left transition hover:bg-white/[0.04]"
            onClick={() => setLogoutOpen(true)}
            type="button"
          >
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indigo-300/10 text-sm font-semibold text-indigo-200">
              {initials}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-white">{user.email}</span>
              <span className="block truncate text-xs text-slate-500">Sign out of workspace</span>
            </span>
          </button>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-30 flex min-h-16 items-center justify-between border-b border-[var(--stroke)] bg-[var(--canvas)]/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 lg:hidden">
            <button
              aria-label="Open navigation"
              className="grid h-11 w-11 place-items-center rounded-xl border border-[var(--stroke)] text-slate-300 hover:bg-white/[0.04] hover:text-white"
              onClick={() => setMobileOpen(true)}
              type="button"
            >
              <span aria-hidden="true" className="text-xl">☰</span>
            </button>
            <Brand compact href="/dashboard" />
          </div>

          <div className="hidden min-w-0 lg:block">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-slate-600">
              Company workspace
            </p>
            <p className="truncate text-sm font-semibold text-slate-200">{user.company.name}</p>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-right sm:block">
              <span className="block max-w-52 truncate text-sm font-medium text-slate-200">{user.email}</span>
              <span className="block text-xs text-emerald-300">Workspace active</span>
            </span>
            <button
              aria-label="Open account menu"
              className="grid h-10 w-10 place-items-center rounded-xl border border-indigo-300/15 bg-indigo-300/10 text-xs font-semibold text-indigo-200"
              onClick={() => setLogoutOpen(true)}
              type="button"
            >
              {initials}
            </button>
          </div>
        </header>
        {children}
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Close navigation"
            className="absolute inset-0 bg-slate-950/75 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            type="button"
          />
          <aside className="relative flex h-full w-[min(88vw,19rem)] flex-col border-r border-[var(--stroke)] bg-[var(--surface-raised)] shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--stroke)] px-5 py-4">
              <Brand compact href="/dashboard" />
              <button
                aria-label="Close navigation"
                className="grid h-10 w-10 place-items-center rounded-xl text-xl text-slate-400 hover:bg-white/5 hover:text-white"
                onClick={() => setMobileOpen(false)}
                type="button"
              >
                ×
              </button>
            </div>
            <div className="border-b border-[var(--stroke)] px-6 py-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-600">Company</p>
              <p className="mt-1 truncate text-sm font-semibold">{user.company.name}</p>
            </div>
            <NavigationContent onNavigate={() => setMobileOpen(false)} />
            <div className="border-t border-[var(--stroke)] p-4">
              <Button className="w-full" onClick={() => setLogoutOpen(true)} variant="secondary">
                Sign out
              </Button>
            </div>
          </aside>
        </div>
      )}

      <Modal
        confirmLabel="Sign out"
        description="You will need to enter your credentials again to access this company workspace."
        onClose={() => setLogoutOpen(false)}
        onConfirm={handleLogout}
        open={logoutOpen}
        title="Sign out of SalesSnap?"
      />
    </div>
  );
}
