"""The read-only, validated tool boundary available to SalesSnap AI chat."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Product
from app.services.anomalies import product_anomalies
from app.services.dashboard import get_summary, get_top_products
from app.services.forecasting import (
    create_product_forecast,
    get_forecast_product,
)
from app.services.rfm import SEGMENTS, analyze_rfm
from app.services.stock_risk import build_stock_risk_result, list_stock_risk_results


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DateRangeArgs(ToolArgs):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must not exceed end_date")
        return self


class TopProductsArgs(DateRangeArgs):
    limit: int = Field(default=5, ge=1, le=10)


class CustomerSegmentsArgs(DateRangeArgs):
    segment: str | None = None

    @model_validator(mode="after")
    def valid_segment(self) -> Self:
        if self.segment is not None and self.segment not in SEGMENTS:
            raise ValueError("Unknown RFM segment")
        return self


class ProductForecastArgs(ToolArgs):
    product_id: uuid.UUID
    horizon: Literal[7, 14, 30] = 30


class AnomaliesArgs(DateRangeArgs):
    product_id: uuid.UUID | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    direction: Literal["spike", "drop"] | None = None
    limit: int = Field(default=10, ge=1, le=10)


class StockRiskArgs(ToolArgs):
    product_id: uuid.UUID | None = None
    risk_level: Literal["critical", "high", "medium", "low", "safe"] | None = None
    horizon: Literal[7, 14, 30] = 30
    limit: int = Field(default=10, ge=1, le=10)


class FindProductArgs(ToolArgs):
    query: str = Field(min_length=1, max_length=255, pattern=r"\S")
    limit: int = Field(default=5, ge=1, le=10)


TOOL_ARGUMENTS: dict[str, type[BaseModel]] = {
    "get_sales_summary": DateRangeArgs,
    "get_top_products": TopProductsArgs,
    "get_customer_segments": CustomerSegmentsArgs,
    "get_product_forecast": ProductForecastArgs,
    "get_sales_anomalies": AnomaliesArgs,
    "get_stock_risk": StockRiskArgs,
    "find_product": FindProductArgs,
}


def tool_definitions() -> list[dict[str, Any]]:
    descriptions = {
        "get_sales_summary": "Get tenant-scoped sales summary metrics.",
        "get_top_products": "Get top products by revenue for a date range.",
        "get_customer_segments": "Get RFM counts and revenue, not churn predictions.",
        "get_product_forecast": "Get a demand forecast for an already identified product UUID.",
        "get_sales_anomalies": "Get detected sales-demand anomalies.",
        "get_stock_risk": "Get computed stock-out risk results.",
        "find_product": "Find products by ID or name within the current company only.",
    }
    return [
        {
            "type": "function",
            "name": name,
            "description": descriptions[name],
            "parameters": _strict_parameters(schema),
            "strict": True,
        }
        for name, schema in TOOL_ARGUMENTS.items()
    ]


def _strict_parameters(schema: type[BaseModel]) -> dict[str, Any]:
    parameters = schema.model_json_schema()
    parameters["required"] = list(parameters["properties"])
    for value in parameters["properties"].values():
        value.pop("default", None)
    return parameters


def execute_tool(
    session: Session, company_id: uuid.UUID, name: str, raw_arguments: dict[str, Any]
) -> dict[str, Any]:
    """Validate a whitelisted tool request and inject the trusted tenant scope."""
    schema = TOOL_ARGUMENTS.get(name)
    if schema is None:
        raise ValueError("Requested tool is not available")
    args = schema.model_validate(raw_arguments)
    return _TOOL_HANDLERS[name](session, company_id, args)


def _sales_summary(session: Session, company_id: uuid.UUID, args: DateRangeArgs) -> dict[str, Any]:
    return get_summary(session, company_id, args.start_date, args.end_date).model_dump(mode="json")


def _top_products(session: Session, company_id: uuid.UUID, args: TopProductsArgs) -> dict[str, Any]:
    return {
        "products": [
            item.model_dump(mode="json")
            for item in get_top_products(
                session, company_id, args.start_date, args.end_date, args.limit
            )
        ]
    }


def _customer_segments(
    session: Session, company_id: uuid.UUID, args: CustomerSegmentsArgs
) -> dict[str, Any]:
    customers, reference_date = analyze_rfm(session, company_id, args.start_date, args.end_date)
    if args.segment:
        customers = [item for item in customers if item.segment == args.segment]
    return {
        "reference_date": reference_date,
        "segments": [
            {
                "segment": name,
                "customers": sum(item.segment == name for item in customers),
                "revenue": str(
                    sum((item.monetary for item in customers if item.segment == name), Decimal("0"))
                ),
            }
            for name in SEGMENTS
            if args.segment is None or name == args.segment
        ],
    }


def _product_forecast(
    session: Session, company_id: uuid.UUID, args: ProductForecastArgs
) -> dict[str, Any]:
    product = get_forecast_product(session, company_id, args.product_id)
    if product is None:
        return {"status": "not_found"}
    return create_product_forecast(session, company_id, product, args.horizon).model_dump(
        mode="json", exclude={"history"}
    )


def _anomalies(session: Session, company_id: uuid.UUID, args: AnomaliesArgs) -> dict[str, Any]:
    products = (
        [get_forecast_product(session, company_id, args.product_id)]
        if args.product_id
        else list(session.scalars(select(Product).where(Product.company_id == company_id)))
    )
    findings: list[dict[str, Any]] = []
    for product in (item for item in products if item is not None):
        items, _ = product_anomalies(
            session, company_id, product, get_settings().anomaly_lookback_days
        )
        items = [
            item
            for item in items
            if (args.start_date is None or item.date >= args.start_date)
            and (args.end_date is None or item.date <= args.end_date)
        ]
        findings.extend(item.model_dump(mode="json") for item in items)
    filtered = [item for item in findings if not args.severity or item["severity"] == args.severity]
    filtered = [
        item for item in filtered if not args.direction or item["direction"] == args.direction
    ]
    filtered.sort(key=lambda item: item["date"], reverse=True)
    return {"anomalies": filtered[: args.limit], "total": len(filtered)}


def _stock_risk(session: Session, company_id: uuid.UUID, args: StockRiskArgs) -> dict[str, Any]:
    if args.product_id:
        product = get_forecast_product(session, company_id, args.product_id)
        results = (
            []
            if product is None
            else [build_stock_risk_result(session, company_id, product, args.horizon)]
        )
    else:
        results, _ = list_stock_risk_results(session, company_id, args.horizon)
    items = [item.model_dump(mode="json", exclude={"projection"}) for item in results]
    if args.risk_level:
        items = [item for item in items if item.get("risk_level") == args.risk_level]
    levels = {
        name: index for index, name in enumerate(("critical", "high", "medium", "low", "safe"))
    }
    items.sort(key=lambda item: (levels.get(item["risk_level"], 5), item["product"]["name"]))
    return {"results": items[: args.limit], "total": len(items)}


def _find_product(session: Session, company_id: uuid.UUID, args: FindProductArgs) -> dict[str, Any]:
    pattern = f"%{args.query}%"
    products = session.scalars(
        select(Product)
        .where(
            Product.company_id == company_id,
            or_(Product.external_id.ilike(pattern), Product.name.ilike(pattern)),
        )
        .order_by(Product.name.asc())
        .limit(args.limit)
    )
    return {
        "products": [
            {"id": item.id, "external_id": item.external_id, "name": item.name} for item in products
        ]
    }


_TOOL_HANDLERS = {
    "get_sales_summary": _sales_summary,
    "get_top_products": _top_products,
    "get_customer_segments": _customer_segments,
    "get_product_forecast": _product_forecast,
    "get_sales_anomalies": _anomalies,
    "get_stock_risk": _stock_risk,
    "find_product": _find_product,
}
