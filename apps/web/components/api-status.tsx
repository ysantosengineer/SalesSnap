"use client";

import { useEffect, useState } from "react";

import { getHealth } from "@/lib/api";

type ApiStatus = "loading" | "online" | "offline";

export function ApiStatus() {
  const [status, setStatus] = useState<ApiStatus>("loading");

  useEffect(() => {
    getHealth().then(() => setStatus("online")).catch(() => setStatus("offline"));
  }, []);

  const label = status === "online" ? "Online" : status === "offline" ? "Offline" : "Checking";

  const tone = status === "online" ? "bg-emerald-400" : status === "offline" ? "bg-rose-400" : "bg-amber-300";

  return (
    <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300">
      <span aria-hidden="true" className={`h-2 w-2 rounded-full ${tone}`} />
      API {label}
    </div>
  );
}
