"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { AuthApiError } from "@/lib/auth-api";
import { useAuth } from "@/components/auth-provider";

export function AuthForm({ mode }: Readonly<{ mode: "login" | "register" }>) {
  const { login, register } = useAuth();
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
        await register(String(formData.get("companyName")), String(formData.get("email")), String(formData.get("password")));
      } else {
        await login(String(formData.get("email")), String(formData.get("password")));
      }
      window.location.assign("/dashboard");
    } catch (cause) {
      setError(cause instanceof AuthApiError ? cause.message : "Unable to continue. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-white">
      <form className="w-full max-w-md space-y-5 rounded-xl border border-slate-700 bg-slate-900 p-8" onSubmit={handleSubmit}>
        <h1 className="text-3xl font-bold">{isRegister ? "Create your workspace" : "Welcome back"}</h1>
        {isRegister && <input aria-label="Company name" className="w-full rounded bg-slate-800 p-3" name="companyName" placeholder="Company name" required />}
        <input aria-label="Email" className="w-full rounded bg-slate-800 p-3" name="email" placeholder="you@company.com" type="email" required />
        <input aria-label="Password" className="w-full rounded bg-slate-800 p-3" name="password" minLength={8} placeholder="Password" type="password" required />
        {error && <p className="text-sm text-rose-300" role="alert">{error}</p>}
        <button className="w-full rounded bg-cyan-500 p-3 font-semibold text-slate-950 disabled:opacity-60" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Please wait..." : isRegister ? "Create account" : "Sign in"}
        </button>
        <p className="text-sm text-slate-300">{isRegister ? "Already have an account?" : "New to SalesSnap?"} <Link className="text-cyan-300" href={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create one"}</Link></p>
      </form>
    </main>
  );
}
