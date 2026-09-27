"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
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

  if (isLoading || user === null) return <main className="p-8">Loading...</main>;

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <section className="mx-auto max-w-2xl space-y-6">
        <div><p className="text-cyan-300">{user.company.name}</p><h1 className="text-3xl font-bold">Upload Sales CSV</h1></div>
        <div className="space-y-4 rounded-xl border border-slate-700 bg-slate-900 p-6">
          <input accept=".csv,text/csv" aria-label="Select CSV" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)} type="file" />
          {file && <p className="text-slate-300">{file.name}</p>}
          <button className="rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60" disabled={file === null || isImporting} onClick={handleImport} type="button">{isImporting ? "Importing..." : "Import Data"}</button>
          {error && <p className="text-rose-300" role="alert">{error}</p>}
        </div>
        <div className="rounded-xl border border-slate-700 p-6"><h2 className="font-semibold">Required columns</h2><code className="mt-3 block whitespace-pre-wrap text-sm text-slate-300">{requiredColumns.join("\n")}</code></div>
        {result && <section className="rounded-xl border border-emerald-700 bg-emerald-950/30 p-6"><h2 className="text-xl font-semibold">Import completed</h2><dl className="mt-4 grid grid-cols-2 gap-3 text-slate-200"><div>Rows received: {result.rows_received}</div><div>Imported: {result.rows_imported}</div><div>Rejected: {result.rows_rejected}</div><div>Products created: {result.products_created}</div><div>Customers created: {result.customers_created}</div><div>Sales created: {result.sales_created}</div></dl>{result.errors.length > 0 && <ul className="mt-5 list-disc pl-5 text-sm text-amber-200">{result.errors.map((item) => <li key={`${item.row}-${item.field}`}>Row {item.row} — {item.message}</li>)}</ul>}</section>}
      </section>
    </main>
  );
}
