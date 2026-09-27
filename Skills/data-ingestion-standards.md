# Data ingestion standards

Stage 4 defines the SalesSnap CSV V1 ingestion contract.

- Accept only UTF-8 CSV files up to `MAX_UPLOAD_SIZE_MB` (10 MB by default). Reject clearly oversized requests from `Content-Length` before multipart parsing, then enforce the exact file limit with bounded chunk reads; never use an unbounded upload read. Excel, JSON, archives, and chunked/background ingestion are out of scope.
- The required columns are exactly `date`, `customer_id`, `product_id`, `product_name`, `quantity`, and `unit_price`. Dates use `YYYY-MM-DD`; quantity is a positive integer; price is a non-negative `Decimal`.
- Pandas reads, normalizes, and validates CSV values. It does not handle HTTP, authentication, database transactions, or authorization.
- The authenticated user's `company_id` is the only tenant source. Never trust a tenant identifier in a request or CSV file.
- Every upload creates a dataset which moves from `pending` to `processing`, then `completed` or `failed`.
- Structural failures fail the entire dataset. Invalid individual rows are rejected while valid rows are persisted; return at most 100 row errors.
- Revenue is always calculated as `quantity * unit_price` using `Decimal`. Product and customer identities are `(company_id, external_id)`.
- Product external IDs are authoritative; a later import may update the product name. Re-uploading a file can create duplicate sales because V1 has no transaction-level deduplication.
- Persist one completed import transaction. On an unexpected persistence failure, roll back data changes and mark the dataset as failed.
- Ingestion creates structured data only. It must not implement dashboards, analytics, segmentation, forecasting, ML, or LLM behavior.
