"use client";

import { type ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, LoadingState } from "@/components/ui/feedback";
import { Card, PageHeader } from "@/components/ui/surface";
import { DatasetImportError, type DatasetImportResult, importDataset } from "@/lib/dataset-api";

const requiredColumns = ["date", "customer_id", "product_id", "product_name", "quantity", "unit_price"];

export default function ImportPage() {
  const { accessToken, isLoading, user } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [result, setResult] = useState<DatasetImportResult | null>(null);

  useEffect(() => {
    if (!isLoading && user === null) router.replace("/login");
  }, [isLoading, router, user]);

  async function handleImport() {
    if (file === null || accessToken === null) return;
    setError(null);
    setResult(null);
    setIsImporting(true);
    try {
      setResult(await importDataset(file, accessToken));
    } catch (cause) {
      setError(cause instanceof DatasetImportError ? cause.message : "CSV import failed");
    } finally {
      setIsImporting(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setError(null);
    setResult(null);
  }

  if (isLoading || user === null) {
    return <LoadingState label="Preparing sales import..." />;
  }

  return (
    <main className="min-h-screen px-5 py-8 text-white sm:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <PageHeader
          description="Add commercial history using a validated CSV file. Valid rows are saved even when individual records are rejected."
          eyebrow={user.company.name}
          title="Import sales data"
        />

        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
          <Card className="space-y-5">
            <div>
              <h2 className="text-lg font-semibold">Choose your CSV</h2>
              <p className="mt-1 text-sm leading-6 text-slate-400">
                Files are validated before processing. The maximum accepted size is 10 MB.
              </p>
            </div>

            <label className="group flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--stroke-strong)] bg-white/[0.02] px-5 text-center transition hover:border-teal-300/50 hover:bg-teal-300/[0.03]">
              <span
                aria-hidden="true"
                className="grid h-11 w-11 place-items-center rounded-2xl bg-teal-300/10 text-xl text-teal-200"
              >
                ↑
              </span>
              <span className="mt-3 text-sm font-semibold text-white">
                {file ? file.name : "Select a sales CSV file"}
              </span>
              <span className="mt-1 text-xs text-slate-500">CSV only · up to 10 MB</span>
              <input
                accept=".csv,text/csv"
                aria-label="Select sales CSV"
                className="sr-only"
                onChange={handleFileChange}
                type="file"
              />
            </label>

            {error && <Alert tone="danger">{error}</Alert>}

            <Button
              className="w-full sm:w-auto"
              disabled={file === null || isImporting}
              onClick={handleImport}
            >
              {isImporting ? "Importing sales..." : "Import sales data"}
            </Button>
          </Card>

          <Card>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold">Required columns</h2>
              <Badge tone="brand">6 fields</Badge>
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
                <h2 className="text-xl font-semibold">Import completed</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Your accepted records are ready for analysis.
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
                ["Products created", result.products_created],
                ["Customers created", result.customers_created],
                ["Sales created", result.sales_created],
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
                  {result.errors.map((item) => (
                    <li key={`${item.row}-${item.field}`}>
                      Row {item.row} — {item.message}
                    </li>
                  ))}
                </ul>
              </Alert>
            )}
          </Card>
        )}
      </div>
    </main>
  );
}
