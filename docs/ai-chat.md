# SalesSnap AI Chat

AI Chat is a read-only analytics copilot for authenticated SalesSnap users. It interprets facts calculated by existing application services; it does not calculate business metrics itself, query PostgreSQL directly, or perform actions.

## Architecture and lifecycle

```text
User question
  → authenticated user and tenant
  → bounded application-owned history
  → OpenAI tool selection
  → SalesSnap tool registry
  → strict Pydantic validation
  → tenant-aware analytics service
  → structured bounded result
  → OpenAI interpretation
  → persisted answer and evidence
  → /chat UI
```

The centralized Stage 10 OpenAI provider is reused. SalesSnap supplies strict function definitions, preserves each function call and `call_id`, executes application code itself, then returns the matching function output. The model never executes internal code.

## Conversation domain and ownership

`ChatConversation` belongs to one company and one user. `ChatMessage` belongs to one conversation and permits only `user` and `assistant` roles. Reads and writes require the conversation ID, authenticated `company_id`, and authenticated `user_id`; cross-user and cross-tenant access returns 404.

PostgreSQL stores the full conversation history for the UI. Only the latest `AI_CHAT_HISTORY_MESSAGES` messages, ten by default, enter a provider request. The first question creates a deterministic title of at most 80 characters. Provider failures keep the user's question but do not persist a false assistant answer.

## Controlled tools

| Tool | Existing capability | Maximum result size |
|---|---|---:|
| `get_sales_summary` | Dashboard summary | One summary |
| `get_top_products` | Dashboard top products | 10 products |
| `get_customer_segments` | RFM segmentation and revenue | Seven segment summaries |
| `get_product_forecast` | Stage 7 forecast | One product; 7, 14, or 30 days |
| `get_sales_anomalies` | Stage 8 anomaly detection | 10 findings |
| `get_stock_risk` | Stage 9 stock-out risk | 10 results |
| `find_product` | Tenant product lookup | 10 products |

Every tool rejects unknown arguments. The model cannot send `company_id`, `user_id`, database URLs, or unrestricted filters. Product lookup and analytics always resolve within the authenticated company.

`AI_CHAT_MAX_TOOL_CALLS`, five by default, is a global per-message budget and counts each call, including calls returned together. Results are limited before they are sent back to the model to control tokens, cost, latency, and hallucination surface.

## Evidence and security

Evidence records are derived server-side from the actual tool results, not invented by the model. Bounded evidence and friendly tool labels are stored with each assistant message, returned by the conversation API, and rendered after a page reload.

Imported strings, product names, identifiers, and tool results are untrusted data. They cannot add a tool, execute SQL, reveal secrets, or override the system prompt. The registry contains no database, write, web-search, inventory mutation, email, or purchase-order tool.

The provider receives no OpenAI key, JWT secret, password hash, refresh token, or database URL as message content. CI and automated tests always mock the provider; a real OpenAI request is manual and opt-in.

## API and UI

- `POST /api/v1/chat/conversations` creates a user-owned conversation.
- `GET /api/v1/chat/conversations` lists only the authenticated user's conversations by latest activity.
- `GET /api/v1/chat/conversations/{id}` returns the owned conversation, messages, evidence, and tools used.
- `POST /api/v1/chat/conversations/{id}/messages` accepts a trimmed message from 1 to 4,000 characters.
- `/chat` provides responsive conversation navigation, suggestions, persisted history, sending feedback, retry, AI-disabled feedback, tool labels, and collapsible evidence.

## Configuration

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
AI_INSIGHTS_ENABLED=false
AI_INSIGHTS_TIMEOUT_SECONDS=30
AI_CHAT_HISTORY_MESSAGES=10
AI_CHAT_MAX_TOOL_CALLS=5
AI_CHAT_MAX_OUTPUT_TOKENS=800
```

Generated output is bounded by `AI_CHAT_MAX_OUTPUT_TOKENS`. When AI is disabled or unavailable, the API returns a controlled 503 response and the UI keeps the conversation recoverable.

## Limitations

V1 is non-streaming and has no RAG, embeddings, web access, arbitrary SQL, write actions, long-term semantic memory, conversation summarization, sharing, search, tags, or autonomous behavior. RFM At Risk is not a churn prediction; anomaly results do not prove causes; forecasts remain Stage 7 model outputs. A human remains responsible for decisions.
