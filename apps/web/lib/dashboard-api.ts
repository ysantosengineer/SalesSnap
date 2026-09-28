const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type DashboardSummary = { total_revenue: string; units_sold: string; sales_records: number; active_customers: number; average_sale_value: string };
export type RevenuePoint = { date: string; revenue: string; units_sold: string; sales_records: number };
export type TopProduct = { product_id: string; external_id: string; name: string; revenue: string; units_sold: string; sales_records: number };
export type DashboardOverview = { latest_dataset: { name: string; status: string; created_at: string } | null };
export type DashboardData = { summary: DashboardSummary; series: RevenuePoint[]; products: TopProduct[]; overview: DashboardOverview };

async function get<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { headers: { Authorization: `Bearer ${accessToken}` }, credentials: "include" });
  if (!response.ok) throw new Error("Unable to load dashboard data.");
  return response.json() as Promise<T>;
}

export async function getDashboard(accessToken: string, startDate?: string, endDate?: string): Promise<DashboardData> {
  const params = new URLSearchParams();
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  const query = params.size ? `?${params}` : "";
  const [summary, series, products, overview] = await Promise.all([
    get<DashboardSummary>(`/dashboard/summary${query}`, accessToken),
    get<RevenuePoint[]>(`/dashboard/revenue-series${query}`, accessToken),
    get<TopProduct[]>(`/dashboard/top-products${query}`, accessToken),
    get<DashboardOverview>(`/dashboard/overview${query}`, accessToken),
  ]);
  return { summary, series, products, overview };
}
