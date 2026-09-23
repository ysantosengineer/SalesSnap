"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/auth-provider";

export default function DashboardPage() {
  const { isLoading, logout, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user === null) router.replace("/login");
  }, [isLoading, router, user]);

  if (isLoading || user === null) return <main className="p-8">Loading...</main>;

  return (
    <main className="min-h-screen bg-slate-950 p-8 text-white">
      <div className="mx-auto flex max-w-4xl items-start justify-between">
        <section>
          <p className="text-cyan-300">{user.company.name}</p>
          <h1 className="mt-2 text-3xl font-bold">SalesSnap dashboard</h1>
          <p className="mt-3 text-slate-300">Signed in as {user.email}</p>
        </section>
        <button className="rounded border border-slate-600 px-4 py-2" onClick={async () => { await logout(); router.replace("/login"); }}>Sign out</button>
      </div>
    </main>
  );
}
