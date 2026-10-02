"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/auth-provider";

const links = [
  ["Dashboard", "/dashboard"],
  ["Import Sales", "/import"],
  ["Inventory", "/inventory"],
  ["Segments", "/customers/segments"],
  ["Forecast", "/forecast"],
  ["Anomalies", "/anomalies"],
  ["Stock Risk", "/stock-risk"],
  ["AI Insights", "/insights"],
  ["AI Chat", "/chat"],
] as const;

export function AppNavigation() {
  const pathname = usePathname();
  const { isLoading, user } = useAuth();
  if (isLoading || !user || pathname === "/" || pathname === "/login" || pathname === "/register") {
    return null;
  }

  return (
    <nav
      aria-label="SalesSnap modules"
      className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/95 px-4 py-3 text-white backdrop-blur"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-2 overflow-x-auto">
        <Link className="mr-2 shrink-0 font-bold text-cyan-300" href="/dashboard">
          SalesSnap
        </Link>
        {links.map(([label, href]) => (
          <Link
            aria-current={pathname === href ? "page" : undefined}
            className={`shrink-0 rounded-lg px-3 py-2 text-sm transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 ${
              pathname === href
                ? "bg-cyan-400 font-semibold text-slate-950"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
            href={href}
            key={href}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
