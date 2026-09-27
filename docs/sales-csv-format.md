# Sales CSV format V1

The first row must contain these required columns:

```csv
date,customer_id,product_id,product_name,quantity,unit_price
2026-09-01,C001,P001,Mouse Logitech,2,149.90
```

| Column | Rule |
| --- | --- |
| `date` | ISO date in `YYYY-MM-DD` format. |
| `customer_id` | Non-empty external customer identifier. |
| `product_id` | Non-empty external product identifier. |
| `product_name` | Non-empty product name. |
| `quantity` | Integer greater than zero. |
| `unit_price` | Decimal greater than or equal to zero. |

`revenue` is not imported: SalesSnap calculates it internally from `quantity * unit_price` using Decimal arithmetic.
