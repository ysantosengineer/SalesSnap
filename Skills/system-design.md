# System design

The intended future data flow is:

```text
User → Company → Datasets → Sales → Analytics → ML Results → AI Insights
```

Expected future domains are authentication, companies, datasets, products, customers, sales, analytics, RFM, forecasting, anomalies, inventory risk, AI insights, and AI chat. This is design documentation only: do not implement these modules in Stage 1.

Keep APIs stateless where practical and the database as the source of truth. Plan future isolation by company. Separate data processing from presentation. An LLM must not replace SQL, Pandas, or ML algorithms; it is primarily an interpretation and natural-language layer. Give modules clear responsibilities and choose simple solutions before distributed infrastructure.

The initial tenancy implementation is shared database, shared schema, and a `company_id` discriminator. A company owns datasets, products, customers, and sales; services must make the tenant scope explicit rather than relying on implicit global context.

AI Chat follows a controlled flow:

```text
Authenticated user
  → user-owned bounded conversation context
  → centralized OpenAI provider
  → controlled tool selection
  → strict Pydantic argument validation
  → server-injected tenant context
  → existing tenant-aware analytics services
  → bounded structured facts
  → OpenAI interpretation
  → persisted evidence-backed answer
```

The LLM cannot access PostgreSQL or SQLAlchemy, choose tenant or user authority, register tools, write business data, browse the web, or execute SQL. PostgreSQL is the source of truth for conversations and messages; the provider does not own conversation history.

CSV ingestion is synchronous in the modular monolith: authenticated upload → parser → Dataset lifecycle → tenant-scoped persistence → import summary. It is intentionally separate from analytics and presentation.

Demand forecasting is on-demand and product-scoped: authenticated tenant → PostgreSQL daily quantity aggregation → Pandas features → scikit-learn evaluation and recursive forecast → API response. Models are not persisted in V1.
