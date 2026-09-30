# SalesSnap AI Chat

AI Chat lets an authenticated user ask natural-language questions about the analytics already available in SalesSnap. Conversations belong to both a company and the individual user; another user or company cannot retrieve them.

The backend persists `ChatConversation` and `ChatMessage` records, loads only a bounded recent history, and sends the model an explicit read-only tool registry. The model can request sales summaries, top products, RFM segment counts, forecasts, anomalies, stock risk, and tenant-scoped product lookup. Arguments are validated with Pydantic and the server injects the company scope.

The model never receives database access, SQL execution, write actions, web search, credentials, or secrets. Tool outputs are returned as application data. Tool loops and generated output are bounded by `AI_CHAT_MAX_TOOL_CALLS` and `AI_CHAT_MAX_OUTPUT_TOKENS`. Factual answers return the tools used and structured evidence.

Configure `OPENAI_API_KEY`, `AI_INSIGHTS_ENABLED`, `AI_CHAT_HISTORY_MESSAGES`, `AI_CHAT_MAX_TOOL_CALLS`, and `AI_CHAT_MAX_OUTPUT_TOKENS` locally. CI uses mocks; it never calls OpenAI.
