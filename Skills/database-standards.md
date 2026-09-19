# Database standards

PostgreSQL is the official database, SQLAlchemy the ORM, and Alembic the migration mechanism. Version migrations; make future schema changes through migrations and never alter production databases manually. Use prepared or parameterized queries.

Add relationships and indexes only with justification. Design toward future multi-company isolation. Do not create domain tables in Stage 1.
