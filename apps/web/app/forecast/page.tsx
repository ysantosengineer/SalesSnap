"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { ForecastProduct, ForecastResult, getForecast, getForecastProducts } from "@/lib/forecast-api";

const horizons = [7, 14, 30];

export default function ForecastPage() {
  const { accessToken, user, isLoading } = useAuth();
  const router = useRouter();
  const [products, setProducts] = useState<ForecastProduct[]>([]);
  const [productId, setProductId] = useState("");
  const [horizon, setHorizon] = useState(30);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { if (!isLoading && !user) router.replace("/login"); }, [isLoading, router, user]);

  const loadProducts = useCallback(() => {
    if (!accessToken) return;
    setLoading(true); setError(null);
    getForecastProducts(accessToken).then((items) => { setProducts(items); setProductId((value) => value || items[0]?.id || ""); }).catch((requestError: Error) => setError(requestError.message)).finally(() => setLoading(false));
  }, [accessToken]);

  const loadForecast = useCallback(() => {
    if (!accessToken || !productId) return;
    setLoading(true); setError(null);
    getForecast(accessToken, productId, horizon).then(setResult).catch((requestError: Error) => setError(requestError.message)).finally(() => setLoading(false));
  }, [accessToken, horizon, productId]);

  useEffect(() => {
    const timer = window.setTimeout(loadProducts, 0);
    return () => window.clearTimeout(timer);
  }, [loadProducts]);
  useEffect(() => {
    if (!productId) return;
    const timer = window.setTimeout(loadForecast, 0);
    return () => window.clearTimeout(timer);
  }, [loadForecast, productId]);

  if (isLoading || !user) return <main className="p-8">Loading...</main>;
  if (products.length === 0 && !loading) return <main className="p-8">No products available for forecasting. <Link className="text-cyan-400" href="/import">Import sales data first.</Link></main>;

  const forecastTotal = result?.forecast.reduce((total, point) => total + Number(point.predicted_quantity), 0) ?? 0;
  return <main className="min-h-screen bg-slate-950 p-6 text-white"><section className="mx-auto max-w-6xl space-y-6"><header><h1 className="text-3xl font-bold">Demand Forecast</h1><p className="text-slate-400">Historical demand and point forecast by product.</p></header><div className="flex flex-wrap gap-3"><select className="rounded bg-slate-800 p-2" value={productId} onChange={(event) => setProductId(event.target.value)}>{products.map((product) => <option key={product.id} value={product.id}>{product.external_id} — {product.name}</option>)}</select><select className="rounded bg-slate-800 p-2" value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}>{horizons.map((days) => <option key={days} value={days}>{days} days</option>)}</select><button className="rounded bg-cyan-400 px-4 text-slate-950" onClick={loadForecast}>Generate</button></div>{loading && <p>Generating forecast...</p>}{error && <div><p className="text-rose-300">{error}</p><button className="underline" onClick={loadForecast}>Retry</button></div>}{result?.status === "insufficient_data" && <section className="rounded border border-amber-500 p-5"><h2 className="font-semibold">Not enough historical data</h2><p>Required: {result.required_observations} days · Available: {result.available_observations} days</p></section>}{result?.status === "ok" && <><section className="grid gap-3 sm:grid-cols-3"><article className="rounded border border-slate-700 p-4"><p>Forecast next {result.horizon_days} days</p><strong>{forecastTotal.toFixed(1)} units</strong></article><article className="rounded border border-slate-700 p-4"><p>Selected model</p><strong>{result.evaluation?.selected_model}</strong></article><article className="rounded border border-slate-700 p-4"><p>Historical observations</p><strong>{result.available_observations} days</strong></article></section><DemandChart result={result} /><section className="rounded border border-slate-700 p-5"><h2 className="font-semibold">Model Quality</h2><div className="mt-3 grid gap-3 sm:grid-cols-3"><p>MAE <strong>{Number(result.evaluation?.mae).toFixed(2)}</strong></p><p>RMSE <strong>{Number(result.evaluation?.rmse).toFixed(2)}</strong></p><p>WAPE <strong>{result.evaluation?.wape === null ? "N/A" : `${(Number(result.evaluation?.wape) * 100).toFixed(1)}%`}</strong></p></div><p className="mt-3 text-sm text-slate-400">MAE is average absolute error. RMSE penalizes larger errors. WAPE is error relative to observed demand.</p></section></>}</section></main>;
}

function DemandChart({ result }: { result: ForecastResult }) {
  const points = [...result.history.map((item) => Number(item.quantity)), ...result.forecast.map((item) => Number(item.predicted_quantity))];
  const max = Math.max(...points, 1);
  const width = 720; const height = 220; const step = width / Math.max(points.length - 1, 1);
  const coordinates = (values: number[], offset = 0) => values.map((value, index) => `${(index + offset) * step},${height - (value / max) * height}`).join(" ");
  return <section className="rounded border border-slate-700 p-5"><h2 className="font-semibold">Historical vs Forecast Demand</h2><svg className="mt-4 w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Historical and forecast demand chart"><polyline fill="none" stroke="#22d3ee" strokeWidth="3" points={coordinates(result.history.map((item) => Number(item.quantity)))} /><polyline fill="none" stroke="#fbbf24" strokeDasharray="6 4" strokeWidth="3" points={coordinates(result.forecast.map((item) => Number(item.predicted_quantity)), Math.max(result.history.length - 1, 0))} /></svg><p className="text-sm text-slate-400"><span className="text-cyan-300">— Historical demand</span> · <span className="text-amber-300">-- Forecast demand</span></p></section>;
}
