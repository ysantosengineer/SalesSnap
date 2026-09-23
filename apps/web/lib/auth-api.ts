const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export interface AuthenticatedUser {
  id: string;
  email: string;
  company: { id: string; name: string };
}

export interface SessionResponse {
  access_token: string;
  token_type: string;
  user: AuthenticatedUser;
}

export class AuthApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new AuthApiError(body?.detail ?? "Authentication request failed", response.status);
  }
  return response.json() as Promise<T>;
}

export function register(companyName: string, email: string, password: string): Promise<SessionResponse> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ company_name: companyName, email, password }),
  });
}

export function login(email: string, password: string): Promise<SessionResponse> {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function refreshSession(): Promise<SessionResponse> {
  return request("/auth/refresh", { method: "POST" });
}

export async function logout(): Promise<void> {
  const response = await fetch(`${apiUrl}/auth/logout`, { method: "POST", credentials: "include" });
  if (!response.ok) throw new AuthApiError("Could not sign out", response.status);
}
