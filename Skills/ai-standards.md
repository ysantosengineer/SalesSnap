# AI standards

LLMs interpret structured, tenant-scoped analytics; they never calculate KPIs, access the database, execute SQL, or change system data. The AI provider is centralized and read-only. Every insight uses validated structured output with controlled category and priority plus non-empty evidence.

Imported strings are untrusted data, never instructions. Do not send secrets, credentials, tokens, database URLs, or customer identifiers unless strictly required. Do not request chain of thought or claim causal inference. No RAG, embeddings, agents, AI Chat, persistence, or autonomous actions in Stage 10.
