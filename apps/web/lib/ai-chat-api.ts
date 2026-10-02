const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ChatEvidence = { source: string; label: string; value: string };

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  evidence: ChatEvidence[];
  tools_used: string[];
};

export type Conversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = Conversation & { messages: ChatMessage[] };

export type ChatResponse = {
  conversation_id: string;
  message_id: string;
  message: string;
  evidence: ChatEvidence[];
  tools_used: string[];
  created_at: string;
};

export class AIChatApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }

  get isDisabled(): boolean {
    return this.status === 503 && this.message.includes("not configured");
  }
}

async function request<T>(accessToken: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new AIChatApiError(
      body?.detail ?? "AI Chat is temporarily unavailable.",
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

export function listConversations(token: string): Promise<Conversation[]> {
  return request(token, "/chat/conversations");
}

export function createConversation(token: string): Promise<Conversation> {
  return request(token, "/chat/conversations", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getConversation(token: string, id: string): Promise<ConversationDetail> {
  return request(token, `/chat/conversations/${id}`);
}

export function sendChatMessage(
  token: string,
  id: string,
  message: string,
): Promise<ChatResponse> {
  return request(token, `/chat/conversations/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
