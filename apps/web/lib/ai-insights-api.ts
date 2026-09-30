const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type AIInsight = { id: string; category: string; priority: string; title: string; summary: string; evidence: string[]; recommended_action: string };
export type AIInsightsResponse = { generated_at: string; insights: AIInsight[] };

export async function generateAIInsights(accessToken: string, start_date?: string, end_date?: string): Promise<AIInsightsResponse> {
  const response = await fetch(`${apiUrl}/analytics/ai-insights/generate`, { method: "POST", headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ start_date: start_date || null, end_date: end_date || null }) });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "AI insights are temporarily unavailable."); }
  return response.json() as Promise<AIInsightsResponse>;
}
