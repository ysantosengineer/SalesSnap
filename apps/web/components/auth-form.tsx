"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Brand } from "@/components/brand";
import { useAuth } from "@/components/auth-provider";
import { AuthApiError } from "@/lib/auth-api";

export function AuthForm({ mode }: Readonly<{ mode: "login" | "register" }>) {
  const { login, register } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    const formData = new FormData(event.currentTarget);
    try {
      if (isRegister) {
        await register(
          String(formData.get("companyName")),
          String(formData.get("email")),
          String(formData.get("password")),
        );
      } else {
        await login(String(formData.get("email")), String(formData.get("password")));
      }
      router.push("/dashboard");
    } catch (cause) {
      setError(cause instanceof AuthApiError ? cause.message : "Unable to continue. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="relative grid min-h-screen overflow-hidden bg-[var(--canvas)] text-white lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden border-r border-white/8 p-12 lg:flex lg:flex-col lg:justify-between">
        <div aria-hidden="true" className="brand-grid absolute inset-0" />
        <div className="relative">
          <Brand />
        </div>
        <div className="relative max-w-xl">
          <div className="mb-6 grid h-12 w-12 place-items-center rounded-2xl border border-indigo-300/15 bg-indigo-400/10 text-xl text-indigo-200">
            ✦
          </div>
          <p className="text-balance text-4xl font-semibold leading-tight tracking-[-0.035em]">
            Decisions feel simpler when every signal lives in one place.
          </p>
          <p className="mt-5 max-w-lg leading-7 text-slate-400">
            Explore sales performance, customer value, demand, anomalies, inventory risk, and
            evidence-backed AI in a workspace built for clarity.
          </p>
        </div>
        <p className="relative text-xs font-medium uppercase tracking-[0.16em] text-slate-600">
          Data · Machine Learning · AI
        </p>
      </section>

      <section className="flex min-h-screen items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden">
            <Brand />
          </div>
          <div className="mb-8">
            <p className="text-sm font-semibold text-teal-300">
              {isRegister ? "Start with a secure workspace" : "Welcome back"}
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">
              {isRegister ? "Create your SalesSnap account" : "Sign in to your workspace"}
            </h1>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              {isRegister
                ? "Your company data stays isolated from every other workspace."
                : "Continue to your analytics, forecasts, and intelligence."}
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {isRegister && (
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-300">Company name</span>
                <input
                  autoComplete="organization"
                  className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-white placeholder:text-slate-600 transition hover:border-[var(--stroke-strong)] focus:border-teal-300 focus:outline-none"
                  name="companyName"
                  placeholder="Acme Commerce"
                  required
                />
              </label>
            )}
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-300">Work email</span>
              <input
                autoComplete="email"
                className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-white placeholder:text-slate-600 transition hover:border-[var(--stroke-strong)] focus:border-teal-300 focus:outline-none"
                name="email"
                placeholder="you@company.com"
                type="email"
                required
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-300">Password</span>
              <input
                autoComplete={isRegister ? "new-password" : "current-password"}
                className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-white placeholder:text-slate-600 transition hover:border-[var(--stroke-strong)] focus:border-teal-300 focus:outline-none"
                name="password"
                minLength={8}
                placeholder={isRegister ? "At least 8 characters" : "Enter your password"}
                type="password"
                required
              />
            </label>
            {error && (
              <div
                className="rounded-xl border border-rose-400/20 bg-rose-400/8 px-4 py-3 text-sm text-rose-200"
                role="alert"
              >
                {error}
              </div>
            )}
            <button
              className="w-full rounded-xl bg-teal-300 px-4 py-3.5 font-semibold text-slate-950 shadow-lg shadow-teal-950/30 transition hover:bg-teal-200 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? "Please wait..." : isRegister ? "Create workspace" : "Sign in"}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-slate-400">
            {isRegister ? "Already have an account?" : "New to SalesSnap?"}{" "}
            <Link
              className="font-semibold text-teal-300 transition hover:text-teal-200"
              href={isRegister ? "/login" : "/register"}
            >
              {isRegister ? "Sign in" : "Create a workspace"}
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
