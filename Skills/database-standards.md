# Database standards

PostgreSQL is the official database, SQLAlchemy the ORM, and Alembic the migration mechanism. Version migrations; make future schema changes through migrations and never alter production databases manually. Use prepared or parameterized queries.

Add relationships and indexes only with justification. Design toward future multi-company isolation. Do not create domain tables in Stage 1.

## Multi-tenancy and data conventions

SalesSnap uses a shared PostgreSQL database and shared schema with `company_id` as the tenant discriminator. Every tenant-owned query must explicitly include `company_id`; cross-company access must return no data. Domain primary keys use UUID consistently. Store money as Python `Decimal` and PostgreSQL `NUMERIC`, never `float`. Audit timestamps are timezone-aware UTC database timestamps with `created_at` and `updated_at` where mutable records require both. Alembic is the sole schema-evolution mechanism.
