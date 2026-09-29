"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { getStockRisk, getStockRiskProduct, getStockRiskSummary, type StockRiskItem, type StockRiskPage, type StockRiskSummary } from "@/lib/stock-risk-api";

const horizons = [7, 14, 30];
const levels = ["", "critical", "high", "medium", "low", "safe"];

export default function StockRiskPage() {
  const { accessToken, isLoading, user } = useAuth();
  const router = useRouter();
  const [horizon, setHorizon] = useState(30);
  const [riskLevel, setRiskLevel] = useState("");
  const [data, setData] = useState<StockRiskPage | null>(null);
  const [summary, setSummary] = useState<StockRiskSummary | null>(null);
  const [detail, setDetail] = useState<StockRiskItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoading && user === null) router.replace("/login");
  }, [isLoading, router, user]);
  useEffect(() => {
    if (!accessToken) return;
    const timer = window.setTimeout(() => {
      setLoading(true); setError(null); setDetail(null);
      Promise.all([getStockRisk(accessToken, horizon, riskLevel), getStockRiskSummary(accessToken, horizon)])
        .then(([items, totals]) => { setData(items); setSummary(totals); })
        .catch((cause: Error) => setError(cause.message))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [accessToken, horizon, riskLevel]);

  async function openProduct(productId: string) {
    if (!accessToken) return;
    try { setDetail(await getStockRiskProduct(accessToken, productId, horizon)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load product."); }
  }

  if (isLoading || user === null) return <main className="p-8">Loading...</main>;
  return <main className="min-h-screen bg-slate-950 p-6 text-white"><section className="mx-auto max-w-6xl space-y-6"><header><p className="text-cyan-300">{user.company.name}</p><h1 className="text-3xl font-bold">Stock-out Risk</h1><p className="text-slate-400">Projected inventory based on the existing demand forecast.</p></header><div className="flex flex-wrap gap-3"><select className="rounded bg-slate-800 p-2" onChange={(event) => setHorizon(Number(event.target.value))} value={horizon}>{horizons.map((days) => <option key={days} value={days}>{days} days</option>)}</select><select className="rounded bg-slate-800 p-2" onChange={(event) => setRiskLevel(event.target.value)} value={riskLevel}>{levels.map((level) => <option key={level} value={level}>{level || "All risk levels"}</option>)}</select></div>{loading && <p>Loading stock-out risk...</p>}{error && <p className="text-rose-300" role="alert">{error}</p>}{summary && <section className="grid gap-3 sm:grid-cols-4"><Metric label="Critical" value={summary.critical}/><Metric label="High" value={summary.high}/><Metric label="Medium" value={summary.medium}/><Metric label="Missing Inventory" value={summary.missing_inventory}/></section>}{data?.items.length === 0 && !loading && <p className="rounded border border-slate-700 p-6">No products match this risk filter.</p>}{data && data.items.length > 0 && <section className="overflow-x-auto rounded border border-slate-700"><table className="w-full text-left text-sm"><thead className="bg-slate-900 text-slate-400"><tr><th className="p-3">Product</th><th>Current Stock</th><th>Forecast Demand</th><th>Days of Cover</th><th>Expected Stock-out</th><th>Risk</th></tr></thead><tbody>{data.items.map((item) => <tr className="border-t border-slate-800 hover:bg-slate-900" key={item.product.id} onClick={() => openProduct(item.product.id)}><td className="cursor-pointer p-3">{item.product.external_id} — {item.product.name}</td><td>{item.current_stock ?? "—"}</td><td>{item.forecast_total ?? "—"}</td><td>{item.days_of_cover ?? "—"}</td><td>{item.expected_stockout_date ?? "—"}</td><td className="capitalize">{item.risk_level ?? item.status.replaceAll("_", " ")}</td></tr>)}</tbody></table></section>}{detail && <section className="rounded border border-slate-700 p-5"><h2 className="text-xl font-semibold">{detail.product.name}</h2><dl className="mt-3 grid gap-2 sm:grid-cols-2"><div>Current Stock: {detail.current_stock ?? "—"}</div><div>Snapshot Date: {detail.snapshot_date ?? "—"}</div><div>Forecast Demand: {detail.forecast_total ?? "—"}</div><div>Projected Shortage: {detail.projected_shortage ?? "—"}</div></dl>{detail.status === "missing_inventory" && <p className="mt-4 text-amber-300">No inventory snapshot available for this product.</p>}{detail.status === "insufficient_data" && <p className="mt-4 text-amber-300">Not enough sales history to estimate stock-out risk.</p>}{detail.status === "success" && <ProjectionChart item={detail}/>}</section>}</section></main>;
}

function Metric({ label, value }: { label: string; value: number }) { return <article className="rounded border border-slate-700 bg-slate-900 p-4"><p className="text-sm text-slate-400">{label}</p><strong className="text-2xl">{value}</strong></article>; }

function ProjectionChart({ item }: { item: StockRiskItem }) { const values = item.projection.map((point) => Number(point.projected_stock)); const min = Math.min(...values, 0); const max = Math.max(...values, 1); const width = 720; const height = 180; const range = max - min || 1; const step = width / Math.max(values.length - 1, 1); const points = values.map((value, index) => `${index * step},${height - ((value - min) / range) * height}`).join(" "); const zeroY = height - ((0 - min) / range) * height; return <div className="mt-5"><h3 className="font-semibold">Projected Inventory</h3><svg className="mt-3 w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Projected inventory chart"><line stroke="#f87171" strokeDasharray="6 4" x1="0" x2={width} y1={zeroY} y2={zeroY}/><polyline fill="none" points={points} stroke="#22d3ee" strokeWidth="3"/></svg><p className="text-sm text-slate-400">Dashed line: zero inventory.</p></div>; }
