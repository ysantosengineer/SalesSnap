const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type StockRiskStatus = "success" | "missing_inventory" | "insufficient_data";
export type StockRiskLevel = "critical" | "high" | "medium" | "low" | "safe";
export type StockRiskItem = {
  status: StockRiskStatus;
  product: { id: string; external_id: string; name: string };
  current_stock: string | null;
  snapshot_date: string | null;
  forecast_total: string | null;
  selected_model: string | null;
  days_of_cover: number | null;
  expected_stockout_date: string | null;
  projected_shortage: string | null;
  risk_level: StockRiskLevel | null;
  projection: { date: string; projected_stock: string }[];
};

export type StockRiskPage = { items: StockRiskItem[]; total: number; limit: number; offset: number };
export type StockRiskSummary = Record<"total_products" | StockRiskLevel | "missing_inventory" | "insufficient_data", number>;

async function request<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    credentials: "include",
  });
  if (!response.ok) throw new Error("Unable to load stock-out risk.");
  return response.json() as Promise<T>;
}

export function getStockRisk(accessToken: string, horizon: number, riskLevel = ""): Promise<StockRiskPage> {
  const filter = riskLevel ? `&risk_level=${riskLevel}` : "";
  return request(`/analytics/stock-risk?horizon=${horizon}${filter}`, accessToken);
}

export function getStockRiskSummary(accessToken: string, horizon: number): Promise<StockRiskSummary> {
  return request(`/analytics/stock-risk/summary?horizon=${horizon}`, accessToken);
}

export function getStockRiskProduct(accessToken: string, productId: string, horizon: number): Promise<StockRiskItem> {
  return request(`/analytics/stock-risk/products/${productId}?horizon=${horizon}`, accessToken);
}
