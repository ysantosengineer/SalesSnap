from decimal import Decimal

import pytest

from app.services.csv_import import CsvStructuralError, parse_sales_csv


def test_parses_valid_sales_csv_and_calculates_decimal_revenue() -> None:
    result = parse_sales_csv(
        b"date,customer_id,product_id,product_name,quantity,unit_price\n"
        b"2026-09-01,C001,P001,Mouse Logitech,2,149.90\n"
    )

    assert result.rows_received == 1
    assert result.errors == []
    assert result.valid_rows[0].unit_price == Decimal("149.90")
    assert result.valid_rows[0].revenue == Decimal("299.80")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "empty"),
        (b"date,customer_id,product_id,product_name,quantity\n", "Missing required columns"),
        (b"date,customer_id,product_id,product_name,quantity,unit_price\n", "no data rows"),
    ],
)
def test_rejects_structurally_invalid_csv(content: bytes, message: str) -> None:
    with pytest.raises(CsvStructuralError, match=message):
        parse_sales_csv(content)


@pytest.mark.parametrize(
    ("row", "field"),
    [
        ("2026-99-99,C001,P001,Mouse,1,10", "date"),
        ("2026-09-01,C001,P001,Mouse,0,10", "quantity"),
        ("2026-09-01,C001,P001,Mouse,-2,10", "quantity"),
        ("2026-09-01,C001,P001,Mouse,abc,10", "quantity"),
        ("2026-09-01,C001,P001,Mouse,1,-10", "unit_price"),
        ("2026-09-01,C001,P001,Mouse,1,abc", "unit_price"),
        ("2026-09-01,,P001,Mouse,1,10", "customer_id"),
        ("2026-09-01,C001,,Mouse,1,10", "product_id"),
    ],
)
def test_rejects_invalid_rows_without_rejecting_valid_rows(row: str, field: str) -> None:
    content = (
        "date,customer_id,product_id,product_name,quantity,unit_price\n"
        f"{row}\n"
        "2026-09-01,C002,P002,Keyboard,1,25.00\n"
    ).encode()
    result = parse_sales_csv(content)

    assert len(result.valid_rows) == 1
    assert result.errors[0].field == field
