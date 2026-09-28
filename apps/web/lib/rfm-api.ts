const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export type RfmCustomer = { customer_id:string; external_id:string; recency:number; frequency:number; monetary:string; r_score:number; f_score:number; m_score:number; fm_score:number; segment:string };
export type RfmSummary = { total_customers:number; segments:{segment:string;customers:number;percentage:string;revenue:string;revenue_percentage:string}[] };
async function get<T>(path:string, token:string):Promise<T>{const response=await fetch(`${apiUrl}${path}`,{headers:{Authorization:`Bearer ${token}`}});if(!response.ok)throw new Error("Unable to load customer segmentation.");return response.json() as Promise<T>}
export const getRfm=(token:string, segment?:string)=>Promise.all([get<RfmSummary>("/analytics/rfm/summary",token),get<{items:RfmCustomer[]}>(`/analytics/rfm/customers${segment?`?segment=${encodeURIComponent(segment)}`:""}`,token)]);
