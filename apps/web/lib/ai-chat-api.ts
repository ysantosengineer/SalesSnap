const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string; created_at: string };
export type Conversation = { id: string; title: string; created_at: string; updated_at: string };
export type ConversationDetail = Conversation & { messages: ChatMessage[] };
export type ChatResponse = { conversation_id: string; message_id: string; message: string; evidence: { source: string; label: string; value: string }[]; tools_used: string[]; created_at: string };

async function request<T>(accessToken: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { ...init, headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json", ...init?.headers }, credentials: "include" });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "AI Chat is temporarily unavailable."); }
  return response.json() as Promise<T>;
}

export const listConversations = (token: string) => request<Conversation[]>(token, "/chat/conversations");
export const createConversation = (token: string) => request<Conversation>(token, "/chat/conversations", { method: "POST", body: JSON.stringify({}) });
export const getConversation = (token: string, id: string) => request<ConversationDetail>(token, `/chat/conversations/${id}`);
export const sendChatMessage = (token: string, id: string, message: string) => request<ChatResponse>(token, `/chat/conversations/${id}/messages`, { method: "POST", body: JSON.stringify({ message }) });
