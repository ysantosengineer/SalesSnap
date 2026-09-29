# Stock-out risk

Stock-out risk combines the latest company-scoped inventory snapshot with the selected Stage 7 demand forecast for a 7-, 14-, or 30-day horizon. It reuses the existing ML-versus-baseline forecasting pipeline and does not train a new model.

For each forecast day, `projected_stock = current_stock - cumulative_forecast`. The first date where projected stock is zero or less is the expected stock-out date. Its one-based day position is days of cover. End-of-horizon shortage is `max(total_forecast - current_stock, 0)`.

Risk is critical through 7 days of cover, high through 14, medium through 30, low when no stock-out happens but remaining stock is at most 20% of current stock, and safe otherwise. Zero stock with forecast demand is critical; zero stock with zero forecast is safe.

`missing_inventory` means a forecast exists but no inventory snapshot exists. `insufficient_data` means Stage 7 cannot forecast because sales history is too short. Neither state is treated as safe.

## API

- `GET /api/v1/analytics/stock-risk`
- `GET /api/v1/analytics/stock-risk/summary`
- `GET /api/v1/analytics/stock-risk/products/{product_id}`

All endpoints derive tenant scope from the authenticated user. List endpoints use a default limit of 25 and maximum of 50 because forecasts are computed on demand.

## Important boundary

Stock-out Risk is **not** Automatic Replenishment. The feature does not include supplier lead times, safety stock, purchase orders, stock movements, reservations, warehouses, forecast uncertainty intervals, or automatic purchasing.
