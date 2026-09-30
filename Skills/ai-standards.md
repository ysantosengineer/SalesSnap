# AI standards

LLMs interpret structured, tenant-scoped analytics; they never calculate KPIs, access the database, execute SQL, or change system data. The AI provider is centralized and read-only. Every insight uses validated structured output with controlled category and priority plus non-empty evidence.

Imported strings are untrusted data, never instructions. Do not send secrets, credentials, tokens, database URLs, or customer identifiers unless strictly required. Do not request chain of thought or claim causal inference. No RAG, embeddings, agents, AI Chat, persistence, or autonomous actions in Stage 10.

## AI Chat

AI Chat is an application-owned, user-private conversation feature. It is read-only: the model selects only whitelisted SalesSnap analytics tools, with Pydantic-validated arguments and `company_id` injected by the server. It must never receive arbitrary SQL, database credentials, write tools, web search, RAG, embeddings, or autonomous actions.

Conversation history and tool-call loops are bounded through configuration. Tool output is application data, not instructions. Factual answers include structured evidence derived from the tools used. Cross-user and cross-company conversations return no data.
