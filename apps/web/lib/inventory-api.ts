const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type InventoryImportResult = {
  rows_received: number;
  rows_imported: number;
  rows_rejected: number;
  snapshots_created: number;
  snapshots_updated: number;
  errors: string[];
};

export async function importInventory(file: File, accessToken: string): Promise<InventoryImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${apiUrl}/inventory/import`, {
    method: "POST",
    body: formData,
    headers: { Authorization: `Bearer ${accessToken}` },
    credentials: "include",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new Error(typeof body?.detail === "string" ? body.detail : "Inventory import failed.");
  }
  return response.json() as Promise<InventoryImportResult>;
}
