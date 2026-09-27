const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type RowError = { row: number; field: string; message: string };

export type DatasetImportResult = {
  dataset_id: string;
  status: string;
  rows_received: number;
  rows_imported: number;
  rows_rejected: number;
  products_created: number;
  customers_created: number;
  sales_created: number;
  errors: RowError[];
};

export class DatasetImportError extends Error {
  constructor(message: string) {
    super(message);
  }
}

export async function importDataset(file: File, accessToken: string): Promise<DatasetImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${apiUrl}/datasets/import`, {
    method: "POST",
    body: formData,
    headers: { Authorization: `Bearer ${accessToken}` },
    credentials: "include",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : "CSV import failed";
    throw new DatasetImportError(message);
  }
  return response.json() as Promise<DatasetImportResult>;
}
