const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type Anomaly = { date: string; product: { id: string; external_id: string; name: string }; actual_demand: string; expected_demand: string; deviation_percentage: string | null; direction: "spike" | "drop"; severity: "low" | "medium" | "high" | "critical"; confidence: "confirmed" | "potential"; statistical_flag: boolean; isolation_forest_flag: boolean };
export type AnomalyPage = { status: "ok" | "insufficient_data"; items: Anomaly[]; total: number; required_observations: number; available_observations: number };
export type ProductAnomalyPage = AnomalyPage & { history: { date: string; quantity: string }[] };
export type AnomalySummary = { total_anomalies: number; critical: number; high: number; medium: number; low: number; spikes: number; drops: number };

async function get<T>(path: string, accessToken: string): Promise<T> { const response = await fetch(`${apiUrl}${path}`, { headers: { Authorization: `Bearer ${accessToken}` }, credentials: "include" }); if (!response.ok) throw new Error("Unable to load anomalies."); return response.json() as Promise<T>; }
export const getAnomalies = (accessToken: string, query = "") => get<AnomalyPage>(`/analytics/anomalies${query}`, accessToken);
export const getAnomalySummary = (accessToken: string) => get<AnomalySummary>("/analytics/anomalies/summary", accessToken);
export const getProductAnomalies = (accessToken: string, productId: string, query = "") => get<ProductAnomalyPage>(`/analytics/anomalies/products/${productId}${query}`, accessToken);
