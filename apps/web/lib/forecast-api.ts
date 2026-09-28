const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ForecastProduct = { id: string; external_id: string; name: string; observations: number; forecast_available: boolean };
export type ForecastPoint = { date: string; quantity?: string; predicted_quantity?: string };
export type ForecastResult = {
  status: "ok" | "insufficient_data";
  product: ForecastProduct;
  history: ForecastPoint[];
  forecast: ForecastPoint[];
  evaluation: { selected_model: string; mae: string; rmse: string; wape: string | null; baseline_mae: string; baseline_rmse: string } | null;
  horizon_days: number;
  required_observations: number;
  available_observations: number;
};

async function request<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { headers: { Authorization: `Bearer ${accessToken}` }, credentials: "include" });
  if (!response.ok) throw new Error("Unable to load demand forecast.");
  return response.json() as Promise<T>;
}

export function getForecastProducts(accessToken: string): Promise<ForecastProduct[]> {
  return request("/analytics/forecast/products", accessToken);
}

export function getForecast(accessToken: string, productId: string, horizon: number): Promise<ForecastResult> {
  return request(`/analytics/forecast/products/${productId}?horizon=${horizon}`, accessToken);
}
