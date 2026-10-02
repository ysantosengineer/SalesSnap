"use client";

import { type ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, LoadingState } from "@/components/ui/feedback";
import { Card, PageHeader } from "@/components/ui/surface";
import { importInventory, type InventoryImportResult } from "@/lib/inventory-api";

const requiredColumns = ["snapshot_date", "product_id", "quantity_on_hand"];

export default function InventoryPage() {
  const { accessToken, isLoading, user } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<InventoryImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    if (!isLoading && user === null) router.replace("/login");
  }, [isLoading, router, user]);

  async function handleImport() {
    if (!file || !accessToken) return;
    setImporting(true);
    setError(null);
    setResult(null);
    try {
      setResult(await importInventory(file, accessToken));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Inventory import failed.");
    } finally {
      setImporting(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setError(null);
    setResult(null);
  }

  if (isLoading || user === null) {
    return <LoadingState label="Preparing inventory import..." />;
  }

  return (
    <main className="min-h-screen px-5 py-8 text-white sm:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <PageHeader
          description="Update current stock levels with a dated inventory snapshot. Existing product snapshots for the same date are updated safely."
          eyebrow={user.company.name}
          title="Import inventory"
        />

        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
          <Card className="space-y-5">
            <div>
              <h2 className="text-lg font-semibold">Choose your CSV</h2>
              <p className="mt-1 text-sm leading-6 text-slate-400">
                Products are resolved inside your company workspace before snapshots are saved.
              </p>
            </div>

            <label className="group flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--stroke-strong)] bg-white/[0.02] px-5 text-center transition hover:border-teal-300/50 hover:bg-teal-300/[0.03]">
              <span
                aria-hidden="true"
                className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-300/10 text-xl text-indigo-200"
              >
                ↑
              </span>
              <span className="mt-3 text-sm font-semibold text-white">
                {file ? file.name : "Select an inventory CSV file"}
              </span>
              <span className="mt-1 text-xs text-slate-500">CSV only · up to 10 MB</span>
              <input
                accept=".csv,text/csv"
                aria-label="Select inventory CSV"
                className="sr-only"
                onChange={handleFileChange}
                type="file"
              />
            </label>

            {error && <Alert tone="danger">{error}</Alert>}

            <Button
              className="w-full sm:w-auto"
              disabled={!file || importing}
              onClick={handleImport}
            >
              {importing ? "Importing inventory..." : "Import inventory"}
            </Button>
          </Card>

          <Card>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">Required columns</h2>
              <Badge tone="brand">3 fields</Badge>
            </div>
            <ul className="mt-4 space-y-2">
              {requiredColumns.map((column) => (
                <li
                  className="rounded-lg bg-white/[0.025] px-3 py-2 font-mono text-xs text-slate-300"
                  key={column}
                >
                  {column}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        {result && (
          <Card className="border-emerald-300/20 bg-emerald-300/[0.04]">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">Inventory updated</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Your latest stock position is ready for risk analysis.
                </p>
              </div>
              <Badge tone={result.rows_rejected > 0 ? "warning" : "success"}>
                {result.rows_rejected > 0 ? "Completed with warnings" : "Success"}
              </Badge>
            </div>
            <dl className="mt-5 grid gap-3 sm:grid-cols-3">
              {[
                ["Rows received", result.rows_received],
                ["Imported", result.rows_imported],
                ["Rejected", result.rows_rejected],
                ["Snapshots created", result.snapshots_created],
                ["Snapshots updated", result.snapshots_updated],
              ].map(([label, value]) => (
                <div className="rounded-xl bg-slate-950/35 p-3" key={label}>
                  <dt className="text-xs text-slate-500">{label}</dt>
                  <dd className="mt-1 text-xl font-semibold text-white">{value}</dd>
                </div>
              ))}
            </dl>
            {result.errors.length > 0 && (
              <Alert className="mt-5" tone="warning">
                <p className="font-semibold">Review rejected rows</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {result.errors.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </Alert>
            )}
          </Card>
        )}
      </div>
    </main>
  );
}
