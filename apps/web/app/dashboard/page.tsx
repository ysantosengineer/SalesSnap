"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { DashboardData, getDashboard } from "@/lib/dashboard-api";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const number = new Intl.NumberFormat("pt-BR");

export default function DashboardPage() {
  const { accessToken, isLoading, logout, user } = useAuth();
  const router = useRouter();
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const load = () => {
    if (!accessToken) return;
    setLoading(true); setError(null);
    getDashboard(accessToken, startDate, endDate).then(setData).catch((cause: Error) => setError(cause.message)).finally(() => setLoading(false));
  };
  useEffect(() => { if (!isLoading && !user) router.replace("/login"); }, [isLoading, router, user]);
  useEffect(() => {
    if (!accessToken) return;
    getDashboard(accessToken)
      .then(setData)
      .catch((cause: Error) => setError(cause.message))
      .finally(() => setLoading(false));
  }, [accessToken]);
  if (isLoading || !user) return <main className="p-8">Loading...</main>;
  const summary = data?.summary;
  const maxRevenue = Math.max(...(data?.series.map((point) => Number(point.revenue)) ?? [1]), 1);
  return <main className="min-h-screen bg-slate-950 p-6 text-white"><section className="mx-auto max-w-6xl space-y-6"><header className="flex justify-between"><div><p className="text-cyan-300">{user.company.name}</p><h1 className="text-3xl font-bold">SalesSnap Dashboard</h1><Link className="mt-2 inline-block text-sm text-cyan-300 underline" href="/chat">Open SalesSnap AI Chat</Link></div><button className="rounded border border-slate-600 px-3" onClick={async () => { await logout(); router.replace("/login"); }}>Sign out</button></header><form className="flex gap-3" onSubmit={(event) => { event.preventDefault(); load(); }}><input className="rounded bg-slate-800 p-2" onChange={(e) => setStartDate(e.target.value)} type="date" value={startDate}/><input className="rounded bg-slate-800 p-2" onChange={(e) => setEndDate(e.target.value)} type="date" value={endDate}/><button className="rounded bg-cyan-500 px-4 text-slate-950" type="submit">Apply</button></form>{loading && <p>Loading dashboard...</p>}{error && <div><p className="text-rose-300">{error}</p><button className="underline" onClick={load}>Retry</button></div>}{summary && summary.sales_records === 0 && <div className="rounded border border-slate-700 p-8">No sales data available yet. <Link className="text-cyan-300" href="/import">Import a CSV to start exploring your sales.</Link></div>}{summary && <><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{[["Total Revenue", money.format(Number(summary.total_revenue))],["Units Sold",number.format(Number(summary.units_sold))],["Sales Records",number.format(summary.sales_records)],["Active Customers",number.format(summary.active_customers)],["Average Sale Value",money.format(Number(summary.average_sale_value))]].map(([label,value]) => <article className="rounded border border-slate-700 bg-slate-900 p-4" key={label}><p className="text-sm text-slate-400">{label}</p><strong className="text-xl">{value}</strong></article>)}</div><div className="grid gap-6 lg:grid-cols-2"><section className="rounded border border-slate-700 p-5"><h2 className="font-semibold">Revenue Over Time</h2><div className="mt-5 flex h-48 items-end gap-2">{data?.series.map((point) => <div className="flex flex-1 flex-col items-center" key={point.date}><span className="w-full rounded-t bg-cyan-400" style={{height:`${(Number(point.revenue)/maxRevenue)*100}%`}} title={money.format(Number(point.revenue))}/><small className="mt-2 text-slate-400">{point.date.slice(5)}</small></div>)}</div></section><section className="rounded border border-slate-700 p-5"><h2 className="font-semibold">Top Products</h2><table className="mt-4 w-full text-left text-sm"><thead><tr className="text-slate-400"><th>Product</th><th>Revenue</th><th>Units</th></tr></thead><tbody>{data?.products.map((product) => <tr key={product.product_id}><td>{product.name}</td><td>{money.format(Number(product.revenue))}</td><td>{number.format(Number(product.units_sold))}</td></tr>)}</tbody></table></section></div></>}</section></main>;
}
