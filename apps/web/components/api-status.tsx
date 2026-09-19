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

  return <p className="mt-8 text-sm text-slate-400">API Status: {label}</p>;
}
