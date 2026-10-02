import type { ChatMessage as ChatMessageData } from "@/lib/ai-chat-api";

const toolLabels: Record<string, string> = {
  get_sales_summary: "Sales Dashboard",
  get_top_products: "Top Products",
  get_customer_segments: "Customer Segments",
  get_product_forecast: "Demand Forecast",
  get_sales_anomalies: "Sales Anomalies",
  get_stock_risk: "Stock Risk",
  find_product: "Product Catalog",
};

export function ChatMessage({ message }: Readonly<{ message: ChatMessageData }>) {
  const assistant = message.role === "assistant";
  return (
    <article
      className={assistant
        ? "mr-6 rounded-2xl border border-slate-700 bg-slate-900 p-4 sm:mr-16"
        : "ml-6 rounded-2xl bg-cyan-950 p-4 sm:ml-16"}
    >
      <div className="flex items-center justify-between gap-4">
        <strong className={assistant ? "text-cyan-300" : "text-white"}>
          {assistant ? "SalesSnap AI" : "You"}
        </strong>
        <time className="text-xs text-slate-500" dateTime={message.created_at}>
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </div>
      <p className="mt-2 whitespace-pre-wrap leading-7 text-slate-100">{message.content}</p>
      {message.tools_used.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2" aria-label="Analytics used">
          {message.tools_used.map((tool) => (
            <span
              className="rounded-full border border-cyan-900 bg-cyan-950/60 px-3 py-1 text-xs text-cyan-200"
              key={tool}
            >
              Analyzed {toolLabels[tool] ?? tool}
            </span>
          ))}
        </div>
      )}
      {message.evidence.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-700 bg-slate-950/60 p-3">
          <summary className="cursor-pointer text-sm font-medium text-slate-300">
            View evidence ({message.evidence.length})
          </summary>
          <dl className="mt-3 grid gap-2 text-sm">
            {message.evidence.map((item, index) => (
              <div
                className="grid gap-1 sm:grid-cols-[minmax(0,1fr)_auto]"
                key={`${item.source}-${item.label}-${index}`}
              >
                <dt className="break-words text-slate-400">
                  {item.label || toolLabels[item.source] || item.source}
                </dt>
                <dd className="break-all font-medium text-slate-100">{item.value}</dd>
              </div>
            ))}
          </dl>
        </details>
      )}
    </article>
  );
}
