# Architecture

```text
Browser
   │
   ▼
Next.js
   │ REST API
   ▼
FastAPI
   ├── PostgreSQL
   ├── Pandas
   ├── Machine Learning
   └── OpenAI API
```

Next.js owns the user interface and experience. FastAPI owns the API, business rules, and orchestration. PostgreSQL is the persisted-data source of truth. Pandas transforms and analyzes data; machine-learning libraries provide predictive and analytical models; OpenAI interprets results and supports natural language.

SalesSnap starts as a modular monolith. Do not introduce microservices without a demonstrated future need.
