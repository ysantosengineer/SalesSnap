# CSV data ingestion

SalesSnap Stage 4 imports sales CSV files through `POST /api/v1/datasets/import`. The endpoint is authenticated and derives the tenant exclusively from the JWT user context.

The upload creates a Dataset, progresses through `pending`, `processing`, and `completed`, and returns a summary. Structural file errors leave the Dataset as `failed`. Valid rows are persisted even when other rows are rejected; responses include up to 100 row errors.

Pandas parses and normalizes the file, while the import service owns Dataset lifecycle, SQLAlchemy persistence, tenant-scoped product/customer resolution, and transaction handling. Product names are updated when a known product external ID is imported with a newer name. Re-importing the same file can create duplicate sales because this version has no sale identifier or deduplication strategy.

The 10 MB default is enforced in two layers: clearly oversized requests are rejected from `Content-Length` before multipart form parsing, while uploads near the boundary are read in 64 KiB chunks and interrupted immediately after the actual file limit is exceeded. The application never performs an unbounded upload read.

Limitations: CSV only; 10 MB default maximum; fixed V1 schema; synchronous processing; no Excel; no background jobs; no duplicate-sale detection.
