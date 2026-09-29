# Inventory snapshots

SalesSnap stores company-scoped point-in-time inventory quantities. An inventory CSV contains:

```csv
snapshot_date,product_id,quantity_on_hand
2026-09-29,P001,120
```

`product_id` is resolved within the authenticated company. Re-importing the same product and date updates its snapshot; quantities must be non-negative. The latest snapshot is the record with the newest `snapshot_date` for the authenticated company and product.

## Important boundary

An Inventory Snapshot is **not** an Inventory Ledger. This version does not model stock movements, reservations, warehouses, purchase orders, suppliers, or historical reconciliation of movements.
