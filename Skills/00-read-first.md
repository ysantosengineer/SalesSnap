# Read first

SalesSnap is a SaaS sales-intelligence product. It will progressively combine commercial data, analytics, machine learning, and natural-language insights to help sales teams make decisions.

`/Skills` is the permanent source of project engineering instructions. Before starting any development stage, read **every** Markdown file in this directory, inspect the repository, and preserve existing decisions. Document an official architectural change in the relevant Skill; do not silently change architecture. Do not anticipate future-stage features: favor simplicity and incremental evolution. Make small, meaningful commits for each logical unit.

Authentication decisions are permanent project rules and are documented in `authentication-standards.md`; read it together with every other Skill before modifying authentication or protected APIs.

Data-import decisions are permanent project rules and are documented in `data-ingestion-standards.md`; read it together with every other Skill before modifying CSV ingestion or Dataset persistence.

Analytics decisions are permanent project rules and are documented in `analytics-standards.md`; read it together with every other Skill before modifying dashboard metrics or analytics queries.

Customer Analytics and RFM decisions are permanent project rules and are documented in `customer-analytics-standards.md`; read it together with every other Skill before modifying customer segmentation, RFM scores, or related endpoints.

Machine-learning and demand-forecasting decisions are permanent project rules in `ml-standards.md`; read it before changing forecasting, analytical models, features, or metrics.

Inventory snapshot and stock-out-risk decisions are permanent project rules in `inventory-analytics-standards.md`; read it before changing inventory imports, projected inventory, or stock risk.

Generative-AI decisions are permanent project rules in `ai-standards.md`; read it before changing AI context, providers, prompts, or insights.

Production configuration, deployment, observability, dependency, and release decisions are permanent project rules in `production-standards.md`; read it before changing runtime hardening, containers, health checks, CI gates, or operational procedures.

Visual identity, interface components, responsive behavior, feedback states, and application navigation are permanent project rules in `design-system-standards.md`; read it before creating or changing frontend UI.

Before starting any development stage:

1. Read every Markdown file inside /Skills.
2. Inspect the current repository state.
3. Understand the scope of the requested stage.
4. Do not implement features outside the current stage.
5. Break the stage into small logical units of work.
6. Validate and commit each logical unit independently.
7. Update the relevant Skills whenever an architectural decision changes.
