"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
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

  if (isLoading || user === null) return <main className="p-8">Loading...</main>;

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <section className="mx-auto max-w-2xl space-y-6">
        <header><p className="text-cyan-300">{user.company.name}</p><h1 className="text-3xl font-bold">Inventory Snapshot</h1></header>
        <section className="space-y-4 rounded-xl border border-slate-700 bg-slate-900 p-6">
          <input accept=".csv,text/csv" aria-label="Select CSV" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)} type="file" />
          {file && <p className="text-slate-300">{file.name}</p>}
          <button className="rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60" disabled={!file || importing} onClick={handleImport} type="button">{importing ? "Importing..." : "Import Inventory"}</button>
          {error && <p className="text-rose-300" role="alert">{error}</p>}
        </section>
        <section className="rounded-xl border border-slate-700 p-6"><h2 className="font-semibold">Required columns</h2><code className="mt-3 block whitespace-pre-wrap text-sm text-slate-300">{requiredColumns.join("\n")}</code></section>
        {result && <section className="rounded-xl border border-emerald-700 bg-emerald-950/30 p-6"><h2 className="text-xl font-semibold">Import completed</h2><dl className="mt-4 grid grid-cols-2 gap-3 text-slate-200"><div>Rows received: {result.rows_received}</div><div>Imported: {result.rows_imported}</div><div>Rejected: {result.rows_rejected}</div><div>Created: {result.snapshots_created}</div><div>Updated: {result.snapshots_updated}</div></dl>{result.errors.length > 0 && <ul className="mt-5 list-disc pl-5 text-sm text-amber-200">{result.errors.map((error) => <li key={error}>{error}</li>)}</ul>}</section>}
      </section>
    </main>
  );
}
