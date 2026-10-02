"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/feedback";
import { Input } from "@/components/ui/field";
import { Card, PageHeader } from "@/components/ui/surface";
import { Table, TableFrame } from "@/components/ui/table";
import { type DashboardData, getDashboard } from "@/lib/dashboard-api";

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const number = new Intl.NumberFormat("pt-BR");

export default function DashboardPage() {
  const { accessToken, isLoading, user } = useAuth();
  const router = useRouter();
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (withFilters = true) => {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        setData(await getDashboard(accessToken, withFilters ? startDate : "", withFilters ? endDate : ""));
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    },
    [accessToken, endDate, startDate],
  );

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, router, user]);

  useEffect(() => {
    if (!accessToken) return;
    getDashboard(accessToken)
      .then(setData)
      .catch((cause: Error) => setError(cause.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  if (isLoading || !user) return <LoadingState label="Preparing your dashboard..." />;

  const summary = data?.summary;
  const maxRevenue = Math.max(...(data?.series.map((point) => Number(point.revenue)) ?? [1]), 1);
  const metrics = summary
    ? [
        ["Total revenue", money.format(Number(summary.total_revenue))],
        ["Units sold", number.format(Number(summary.units_sold))],
        ["Sales records", number.format(summary.sales_records)],
        ["Active customers", number.format(summary.active_customers)],
        ["Average sale", money.format(Number(summary.average_sale_value))],
      ]
    : [];

  return (
    <main className="min-h-screen px-5 py-8 text-white sm:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          actions={
            <Link
              className="inline-flex min-h-11 items-center justify-center rounded-xl bg-teal-300 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-teal-200"
              href="/chat"
            >
              Ask SalesSnap AI
            </Link>
          }
          description="Monitor commercial performance, customer activity and product momentum from one workspace."
          eyebrow="Overview"
          title="Sales dashboard"
        />

        <Card>
          <form
            className="flex flex-col gap-4 sm:flex-row sm:items-end"
            onSubmit={(event) => {
              event.preventDefault();
              void load();
            }}
          >
            <label className="flex-1 text-sm font-medium text-slate-300">
              Start date
              <Input className="mt-2" onChange={(event) => setStartDate(event.target.value)} type="date" value={startDate} />
            </label>
            <label className="flex-1 text-sm font-medium text-slate-300">
              End date
              <Input className="mt-2" onChange={(event) => setEndDate(event.target.value)} type="date" value={endDate} />
            </label>
            <Button className="sm:min-w-28" type="submit">Apply filters</Button>
          </form>
        </Card>

        {loading && <LoadingState label="Loading commercial performance..." />}
        {!loading && error && <ErrorState message={error} onRetry={() => void load()} />}
        {!loading && !error && summary?.sales_records === 0 && (
          <EmptyState
            actionHref="/import"
            actionLabel="Import sales CSV"
            description="Add your first sales dataset to unlock revenue, customer and product analytics."
            title="No sales data yet"
          />
        )}

        {!loading && !error && summary && summary.sales_records > 0 && (
          <>
            <section aria-label="Key performance indicators" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              {metrics.map(([label, value], index) => (
                <Card className="p-4" key={label}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-medium text-slate-500">{label}</p>
                    {index === 0 && <Badge tone="success">Live</Badge>}
                  </div>
                  <p className="mt-3 text-2xl font-semibold tracking-tight text-white">{value}</p>
                </Card>
              ))}
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
              <Card>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h2 className="font-semibold">Revenue over time</h2>
                    <p className="mt-1 text-xs text-slate-500">Daily sales performance in the selected period</p>
                  </div>
                  <Badge tone="brand">Revenue</Badge>
                </div>
                <div className="mt-6 flex h-56 items-end gap-2" role="img" aria-label="Revenue bar chart">
                  {data?.series.map((point) => (
                    <div className="group flex h-full min-w-0 flex-1 flex-col items-center justify-end" key={point.date}>
                      <span
                        className="w-full min-w-2 rounded-t bg-gradient-to-t from-teal-500 to-teal-300 transition group-hover:from-indigo-500 group-hover:to-indigo-300"
                        style={{ height: `${Math.max((Number(point.revenue) / maxRevenue) * 100, 2)}%` }}
                        title={`${point.date}: ${money.format(Number(point.revenue))}`}
                      />
                      <small className="mt-2 hidden text-[0.65rem] text-slate-600 sm:block">{point.date.slice(5)}</small>
                    </div>
                  ))}
                </div>
              </Card>

              <div>
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold">Top products</h2>
                    <p className="mt-1 text-xs text-slate-500">Ranked by generated revenue</p>
                  </div>
                  <Badge>{data?.products.length ?? 0} products</Badge>
                </div>
                <TableFrame>
                  <Table>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Revenue</th>
                        <th>Units</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data?.products.map((product) => (
                        <tr key={product.product_id}>
                          <td>
                            <p className="font-medium text-slate-200">{product.name}</p>
                            <p className="mt-0.5 text-xs text-slate-600">{product.external_id}</p>
                          </td>
                          <td className="font-medium text-white">{money.format(Number(product.revenue))}</td>
                          <td className="text-slate-300">{number.format(Number(product.units_sold))}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </TableFrame>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
