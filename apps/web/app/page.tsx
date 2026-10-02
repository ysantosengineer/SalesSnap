import Link from "next/link";

import { ApiStatus } from "@/components/api-status";
import { Brand } from "@/components/brand";

const metrics = [
  ["Revenue", "R$ 284k", "+18.4%"],
  ["Customers", "1,248", "+12.1%"],
  ["At-risk SKUs", "14", "Review"],
] as const;

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden px-6 pb-16 text-white">
      <div aria-hidden="true" className="brand-grid absolute inset-0" />
      <nav className="relative mx-auto flex max-w-7xl items-center justify-between py-6">
        <Brand />
        <div className="flex items-center gap-2">
          <Link
            className="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-white/5 hover:text-white"
            href="/login"
          >
            Sign in
          </Link>
          <Link
            className="rounded-xl bg-teal-300 px-4 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-teal-500/10 transition hover:bg-teal-200"
            href="/register"
          >
            Start exploring
          </Link>
        </div>
      </nav>

      <section className="relative mx-auto grid max-w-7xl items-center gap-16 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-teal-300/20 bg-teal-300/5 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-teal-200">
            Sales intelligence, clearly explained
          </div>
          <h1 className="text-balance mt-7 max-w-3xl text-5xl font-semibold leading-[1.04] tracking-[-0.045em] sm:text-6xl lg:text-7xl">
            Turn sales data into your next{" "}
            <span className="bg-gradient-to-r from-teal-300 to-indigo-300 bg-clip-text text-transparent">
              confident decision.
            </span>
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">
            One focused workspace for commercial analytics, customer intelligence, demand signals,
            inventory risk, and evidence-backed AI.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link
              className="rounded-xl bg-teal-300 px-5 py-3.5 text-center font-semibold text-slate-950 shadow-xl shadow-teal-950/30 transition hover:-translate-y-0.5 hover:bg-teal-200"
              href="/register"
            >
              Create your workspace
            </Link>
            <Link
              className="rounded-xl border border-slate-600 bg-slate-900/50 px-5 py-3.5 text-center font-semibold text-white transition hover:border-slate-500 hover:bg-slate-800"
              href="/login"
            >
              Open dashboard
            </Link>
          </div>
          <ApiStatus />
        </div>

        <div className="relative">
          <div aria-hidden="true" className="absolute -inset-8 rounded-full bg-indigo-500/10 blur-3xl" />
          <div className="relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-[#0d1527]/90 p-5 shadow-2xl shadow-black/40 backdrop-blur sm:p-7">
            <div className="flex items-center justify-between border-b border-white/10 pb-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Executive overview
                </p>
                <p className="mt-1 text-lg font-semibold">Commercial pulse</p>
              </div>
              <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
                Live signals
              </span>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {metrics.map(([label, value, change]) => (
                <article className="rounded-2xl border border-white/8 bg-white/[0.035] p-4" key={label}>
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className="mt-2 text-xl font-semibold tracking-tight">{value}</p>
                  <p className="mt-1 text-xs text-teal-300">{change}</p>
                </article>
              ))}
            </div>
            <div className="mt-4 rounded-2xl border border-white/8 bg-white/[0.025] p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Revenue trend</p>
                  <p className="mt-1 text-xs text-slate-500">Last 8 weeks</p>
                </div>
                <span className="text-sm font-semibold text-teal-300">+18.4%</span>
              </div>
              <div className="mt-8 flex h-32 items-end gap-2" aria-label="Illustrative revenue chart">
                {[42, 56, 49, 68, 61, 79, 72, 92].map((height, index) => (
                  <div
                    className="flex-1 rounded-t-md bg-gradient-to-t from-teal-500/60 to-indigo-400"
                    key={height + index}
                    style={{ height: height + "%" }}
                  />
                ))}
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3 rounded-2xl border border-indigo-300/15 bg-indigo-400/[0.06] p-4">
              <div className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-400/15 text-indigo-200">✦</div>
              <div>
                <p className="text-sm font-medium">Evidence-backed intelligence</p>
                <p className="mt-0.5 text-xs text-slate-400">
                  Every AI answer stays connected to your analytics.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
