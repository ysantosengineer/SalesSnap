import Link from "next/link";

import { ApiStatus } from "@/components/api-status";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
      <section className="max-w-2xl text-center">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300">Sales Intelligence</p>
        <h1 className="text-5xl font-bold tracking-tight sm:text-7xl">SalesSnap</h1>
        <p className="mt-6 text-lg leading-8 text-slate-300">Sales Intelligence powered by Data, Machine Learning and AI.</p>
        <ApiStatus />
        <div className="mt-8 flex justify-center gap-3">
          <Link className="rounded-lg bg-cyan-400 px-5 py-3 font-semibold text-slate-950" href="/login">
            Sign in
          </Link>
          <Link className="rounded-lg border border-slate-600 px-5 py-3 font-semibold" href="/register">
            Create workspace
          </Link>
        </div>
      </section>
    </main>
  );
}
