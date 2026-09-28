"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { getRfm, RfmCustomer, RfmSummary } from "@/lib/rfm-api";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const segments = ["Champions", "Loyal Customers", "Potential Loyalists", "New Customers", "At Risk", "Hibernating", "Need Attention"];

export default function Segments() {
  const { accessToken, user, isLoading } = useAuth();
  const router = useRouter();
  const [summary, setSummary] = useState<RfmSummary | null>(null);
  const [items, setItems] = useState<RfmCustomer[]>([]);
  const [selectedSegment, setSelectedSegment] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, router, user]);

  const load = useCallback(() => {
    if (!accessToken) return;
    getRfm(accessToken, selectedSegment || undefined)
      .then(([nextSummary, customers]) => {
        setError(null);
        setSummary(nextSummary);
        setItems(customers.items);
      })
      .catch((requestError: Error) => setError(requestError.message));
  }, [accessToken, selectedSegment]);

  useEffect(() => {
    load();
  }, [load]);

  if (isLoading || !user) return <main className="p-8">Loading...</main>;
  if (error) return <main className="p-8">{error} <button onClick={load}>Retry</button></main>;
  if (summary?.total_customers === 0) return <main className="p-8">No customer data available yet. <Link href="/import">Import sales data</Link></main>;

  return <main className="min-h-screen bg-slate-950 p-6 text-white"><section className="mx-auto max-w-6xl"><h1 className="text-3xl font-bold">Customer Segmentation</h1><select className="my-5 bg-slate-800 p-2" onChange={(event) => setSelectedSegment(event.target.value)} value={selectedSegment}><option value="">All Segments</option>{segments.map((item) => <option key={item}>{item}</option>)}</select><div className="grid gap-3 sm:grid-cols-3">{summary?.segments.map((item) => <article className="rounded border border-slate-700 p-4" key={item.segment}><b>{item.segment}</b><p>{item.customers} customers</p><p>{money.format(Number(item.revenue))}</p></article>)}</div><table className="mt-8 w-full text-left"><thead><tr><th>Customer</th><th>R</th><th>F</th><th>M</th><th>Recency</th><th>Frequency</th><th>Monetary</th><th>Segment</th></tr></thead><tbody>{items.map((customer) => <tr key={customer.customer_id}><td>{customer.external_id}</td><td>{customer.r_score}</td><td>{customer.f_score}</td><td>{customer.m_score}</td><td>{customer.recency}</td><td>{customer.frequency}</td><td>{money.format(Number(customer.monetary))}</td><td>{customer.segment}</td></tr>)}</tbody></table></section></main>;
}
