"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { ChatMessage } from "@/components/chat-message";
import {
  AIChatApiError,
  type Conversation,
  type ConversationDetail,
  createConversation,
  getConversation,
  listConversations,
  sendChatMessage,
} from "@/lib/ai-chat-api";

const suggestions = [
  "How are my sales performing?",
  "Which products have the highest stock-out risk?",
  "Show my customer segments.",
  "Were there important anomalies recently?",
  "What is the forecast for P001?",
];

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export default function ChatPage() {
  const { accessToken, isLoading: authLoading, user } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<ConversationDetail | null>(null);
  const [message, setMessage] = useState("");
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiDisabled, setAiDisabled] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, router, user]);

  const loadConversation = useCallback(async (id: string) => {
    if (!accessToken) return;
    setConversationLoading(true);
    setError(null);
    try {
      setActive(await getConversation(accessToken, id));
    } catch (cause) {
      setError(errorMessage(cause, "Unable to load this conversation."));
    } finally {
      setConversationLoading(false);
    }
  }, [accessToken]);

  const loadConversations = useCallback(async () => {
    if (!accessToken) return;
    setListLoading(true);
    setError(null);
    try {
      const items = await listConversations(accessToken);
      setConversations(items);
      if (items.length > 0) await loadConversation(items[0].id);
    } catch (cause) {
      setError(errorMessage(cause, "Unable to load conversations."));
    } finally {
      setListLoading(false);
    }
  }, [accessToken, loadConversation]);

  useEffect(() => {
    if (!accessToken) return;
    const token = accessToken;
    let cancelled = false;

    async function loadInitialConversations() {
      try {
        const items = await listConversations(token);
        if (cancelled) return;
        setConversations(items);
        if (items.length > 0) {
          const conversation = await getConversation(token, items[0].id);
          if (!cancelled) setActive(conversation);
        }
      } catch (cause) {
        if (!cancelled) setError(errorMessage(cause, "Unable to load conversations."));
      } finally {
        if (!cancelled) setListLoading(false);
      }
    }

    void loadInitialConversations();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function newChat() {
    if (!accessToken || creating) return;
    setCreating(true);
    setError(null);
    try {
      const conversation = await createConversation(accessToken);
      setConversations((items) => [conversation, ...items]);
      setActive({ ...conversation, messages: [] });
      setMessage("");
      setLastFailedMessage(null);
      setAiDisabled(false);
    } catch (cause) {
      setError(errorMessage(cause, "Unable to create a conversation."));
    } finally {
      setCreating(false);
    }
  }

  async function send(text: string) {
    if (!accessToken || !active || !text.trim() || sending) return;
    const content = text.trim();
    setMessage("");
    setSending(true);
    setError(null);
    setAiDisabled(false);
    setLastFailedMessage(null);
    try {
      await sendChatMessage(accessToken, active.id, content);
      const refreshed = await getConversation(accessToken, active.id);
      setActive(refreshed);
      setConversations((items) => [
        {
          id: refreshed.id,
          title: refreshed.title,
          created_at: refreshed.created_at,
          updated_at: refreshed.updated_at,
        },
        ...items.filter((item) => item.id !== refreshed.id),
      ]);
    } catch (cause) {
      setLastFailedMessage(content);
      if (cause instanceof AIChatApiError && cause.isDisabled) setAiDisabled(true);
      setError(errorMessage(cause, "I couldn't analyze your data right now."));
      try {
        setActive(await getConversation(accessToken, active.id));
      } catch {
        // Preserve the provider error; a manual reload can recover the persisted history.
      }
    } finally {
      setSending(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void send(message);
  }

  if (authLoading || !user) {
    return <main className="min-h-screen bg-slate-950 p-8 text-white">Loading your workspace...</main>;
  }

  return (
    <main className="min-h-screen bg-slate-950 p-4 text-white sm:p-6">
      <section className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-7xl overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl md:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-slate-800 bg-slate-900/70 p-4 md:border-b-0 md:border-r">
          <div className="flex items-start justify-between gap-3 md:block">
            <div>
              <p className="text-sm text-cyan-300">{user.company.name}</p>
              <h1 className="text-xl font-bold">SalesSnap AI</h1>
            </div>
            <Link className="text-sm text-slate-400 underline hover:text-white" href="/dashboard">
              Dashboard
            </Link>
          </div>
          <button
            className="mt-4 w-full rounded-xl bg-cyan-400 p-2.5 font-semibold text-slate-950 disabled:opacity-60"
            disabled={creating}
            onClick={() => void newChat()}
            type="button"
          >
            {creating ? "Creating..." : "+ New Chat"}
          </button>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1 md:block md:space-y-2 md:overflow-visible">
            {listLoading && <p className="text-sm text-slate-400">Loading conversations...</p>}
            {!listLoading && conversations.length === 0 && (
              <p className="text-sm text-slate-500">No conversations yet.</p>
            )}
            {conversations.map((item) => (
              <button
                aria-current={active?.id === item.id ? "page" : undefined}
                className={`min-w-52 rounded-xl p-3 text-left transition md:block md:w-full ${
                  active?.id === item.id
                    ? "bg-slate-700 text-white"
                    : "bg-slate-800/50 text-slate-300 hover:bg-slate-800"
                }`}
                key={item.id}
                onClick={() => void loadConversation(item.id)}
                type="button"
              >
                <span className="block truncate font-medium">{item.title}</span>
                <span className="mt-1 block text-xs text-slate-500">
                  {new Date(item.updated_at).toLocaleString([], {
                    dateStyle: "short",
                    timeStyle: "short",
                  })}
                </span>
              </button>
            ))}
          </div>
        </aside>

        <section className="flex min-h-[640px] min-w-0 flex-col">
          <header className="border-b border-slate-800 p-5">
            <h2 className="text-xl font-semibold">{active?.title ?? "Analytics Copilot"}</h2>
            <p className="mt-1 text-sm text-slate-400">
              Read-only answers grounded in your authorized SalesSnap analytics.
            </p>
          </header>

          <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6" aria-live="polite">
            {conversationLoading && <p className="text-slate-400">Loading messages...</p>}
            {!conversationLoading && active?.messages.map((item) => (
              <ChatMessage key={item.id} message={item} />
            ))}
            {!conversationLoading && active && active.messages.length === 0 && (
              <div className="mx-auto max-w-2xl py-10 text-center">
                <h3 className="text-2xl font-semibold">Ask about your business</h3>
                <p className="mt-2 text-slate-400">
                  SalesSnap uses controlled, tenant-aware analytics tools. It cannot modify data.
                </p>
                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  {suggestions.map((suggestion) => (
                    <button
                      className="rounded-xl border border-slate-700 p-3 text-left text-sm text-slate-300 hover:border-cyan-500 hover:text-white"
                      key={suggestion}
                      onClick={() => setMessage(suggestion)}
                      type="button"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {!active && !conversationLoading && (
              <div className="mx-auto max-w-lg py-20 text-center text-slate-400">
                <p>
                  Create a conversation to analyze sales, customers, forecasts, anomalies, and
                  stock risk.
                </p>
                <button
                  className="mt-4 text-cyan-300 underline"
                  onClick={() => void newChat()}
                  type="button"
                >
                  Start a new chat
                </button>
              </div>
            )}
            {sending && (
              <div className="mr-16 animate-pulse rounded-2xl bg-slate-900 p-4 text-slate-300">
                Analyzing your SalesSnap data...
              </div>
            )}
          </div>

          <div className="border-t border-slate-800 p-4 sm:p-5">
            {error && (
              <div className="mb-3 rounded-xl border border-rose-900 bg-rose-950/40 p-3 text-sm">
                <p>{aiDisabled ? "AI Chat is not configured for this environment." : error}</p>
                {!aiDisabled && lastFailedMessage && (
                  <button
                    className="mt-2 font-medium text-rose-200 underline disabled:opacity-60"
                    disabled={sending}
                    onClick={() => void send(lastFailedMessage)}
                    type="button"
                  >
                    Retry
                  </button>
                )}
                {!lastFailedMessage && (
                  <button
                    className="mt-2 text-rose-200 underline"
                    onClick={() => void loadConversations()}
                    type="button"
                  >
                    Reload
                  </button>
                )}
              </div>
            )}
            <form className="flex gap-2" onSubmit={submit}>
              <label className="sr-only" htmlFor="chat-message">Ask SalesSnap</label>
              <textarea
                className="min-h-12 min-w-0 flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900 p-3 outline-none focus:border-cyan-500 disabled:opacity-60"
                disabled={!active || sending || aiDisabled}
                id="chat-message"
                maxLength={4000}
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
                placeholder={aiDisabled ? "AI Chat is not configured" : "Ask SalesSnap..."}
                rows={1}
                value={message}
              />
              <button
                className="rounded-xl bg-cyan-400 px-5 font-semibold text-slate-950 disabled:opacity-60"
                disabled={!active || sending || aiDisabled || !message.trim()}
                type="submit"
              >
                Send
              </button>
            </form>
            <p className="mt-2 text-center text-xs text-slate-500">
              SalesSnap AI is read-only. Verify important business decisions.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}
