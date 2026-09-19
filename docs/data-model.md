# Core data model

```text
Company
 ├── Dataset
 ├── Product
 ├── Customer
 └── Sale
      ├── Dataset
      ├── Product
      └── Customer (optional)
```

SalesSnap uses a shared PostgreSQL database and shared schema. `company_id` scopes every tenant-owned record and tenant-aware service query. Product and customer external identifiers are unique only within one company.

Identifiers are UUIDs. Money uses `Decimal` in Python and `NUMERIC` in PostgreSQL. Timestamps are timezone-aware and managed by the database. Foreign keys intentionally do not cascade deletion: historical sales must not disappear due to an accidental related-record deletion.
