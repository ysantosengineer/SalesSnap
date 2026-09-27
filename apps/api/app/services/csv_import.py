from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from app.schemas.dataset_import import RowError

REQUIRED_COLUMNS = (
    "date",
    "customer_id",
    "product_id",
    "product_name",
    "quantity",
    "unit_price",
)
MAX_RETURNED_ROW_ERRORS = 100


class CsvStructuralError(ValueError):
    """Raised when a file cannot be interpreted as the SalesSnap CSV V1 schema."""


@dataclass(frozen=True)
class ParsedSaleRow:
    sale_date: date
    customer_external_id: str
    product_external_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    revenue: Decimal


@dataclass
class CsvParseResult:
    rows_received: int
    valid_rows: list[ParsedSaleRow] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


def parse_sales_csv(content: bytes) -> CsvParseResult:
    """Read and validate the fixed SalesSnap sales CSV V1 format using Pandas."""
    if not content.strip():
        raise CsvStructuralError("CSV file is empty")
    try:
        frame = pd.read_csv(StringIO(content.decode("utf-8-sig")), dtype=str, keep_default_na=False)
    except (UnicodeDecodeError, EmptyDataError, ParserError) as error:
        raise CsvStructuralError("CSV file is invalid") from error

    frame.columns = [str(column).strip() for column in frame.columns]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise CsvStructuralError(f"Missing required columns: {', '.join(missing_columns)}")
    if frame.empty:
        raise CsvStructuralError("CSV file has no data rows")

    result = CsvParseResult(rows_received=len(frame))
    for index, row in frame.iterrows():
        row_number = int(index) + 2
        parsed_row, error = normalize_row(row, row_number)
        if error is not None:
            if len(result.errors) < MAX_RETURNED_ROW_ERRORS:
                result.errors.append(error)
            continue
        result.valid_rows.append(parsed_row)
    return result


def normalize_row(row: pd.Series, row_number: int) -> tuple[ParsedSaleRow | None, RowError | None]:
    customer_id = value(row, "customer_id")
    product_id = value(row, "product_id")
    product_name = value(row, "product_name")
    for field_name, field_value in (
        ("customer_id", customer_id),
        ("product_id", product_id),
        ("product_name", product_name),
    ):
        if not field_value:
            return None, RowError(
                row=row_number, field=field_name, message=f"{field_name} is required"
            )

    try:
        sale_date = datetime.strptime(value(row, "date"), "%Y-%m-%d").date()
    except ValueError:
        return None, RowError(row=row_number, field="date", message="date must use YYYY-MM-DD")

    try:
        quantity_value = Decimal(value(row, "quantity"))
        if quantity_value <= 0 or quantity_value != quantity_value.to_integral_value():
            raise ValueError
        quantity = int(quantity_value)
    except (InvalidOperation, ValueError):
        return None, RowError(
            row=row_number,
            field="quantity",
            message="quantity must be an integer greater than zero",
        )

    try:
        unit_price = Decimal(value(row, "unit_price"))
        if unit_price < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return None, RowError(
            row=row_number,
            field="unit_price",
            message="unit_price must be a decimal greater than or equal to zero",
        )

    return (
        ParsedSaleRow(
            sale_date=sale_date,
            customer_external_id=customer_id,
            product_external_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            revenue=Decimal(quantity) * unit_price,
        ),
        None,
    )


def value(row: pd.Series, field_name: str) -> str:
    return str(row[field_name]).strip()
