# Inventory analytics standards

Inventory snapshots are company-scoped point-in-time quantities, not an inventory ledger. The authoritative inventory value for a product is the latest `InventorySnapshot` by `snapshot_date`, always filtered by both `company_id` and `product_id`.

- Inventory CSV files contain `snapshot_date`, `product_id`, and `quantity_on_hand`. `product_id` resolves through the tenant-scoped `(company_id, external_id)` identity.
- A re-import for the same company, product, and snapshot date upserts that snapshot. Quantities cannot be negative.
- Missing inventory does not mean zero inventory. A product with an available forecast but no snapshot has `missing_inventory` status and no calculated risk.
- Stock-out risk reuses the selected Stage 7 demand forecast. Do not train a second stock-risk model or duplicate forecast features or model evaluation.
- For each forecast date, projected stock is `current_stock - cumulative_forecast`. The expected stock-out date is the first projected stock at or below zero; days of cover is its one-based forecast-day position. If no such date exists, both values are null.
- Projected shortage is `max(total_forecast - current_stock, 0)` at the end of the selected horizon.
- Risk levels are deterministic: critical at zero stock with demand or stock-out within 7 days; high through 14 days; medium through 30 days; low when no stock-out occurs but projected remaining stock is at most 20% of current stock; otherwise safe. Zero stock with zero forecast is safe.
- Insufficient Stage 7 history is `insufficient_data`, not a risk calculation. Every inventory and forecast lookup must remain tenant-scoped.

Stock-out risk is decision support only. Do not add automated replenishment, purchase orders, supplier logic, safety stock, lead-time optimization, warehouses, reservations, or stock movements without a dedicated stage.
