import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.dashboard import get_summary, get_top_products
from app.services.rfm import analyze_rfm
from app.services.stock_risk import list_stock_risk_results


def build_ai_insight_context(
    session: Session,
    company_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, object]:
    """Build bounded, tenant-scoped facts for AI interpretation only."""
    limit = get_settings().ai_insights_max_items_per_section
    dashboard = get_summary(session, company_id, start_date, end_date)
    rfm, _ = analyze_rfm(session, company_id, start_date, end_date)
    risks, _ = list_stock_risk_results(session, company_id, 30, limit=limit)
    segments: dict[str, dict[str, object]] = {}
    for customer in rfm:
        entry = segments.setdefault(customer.segment, {"customers": 0, "revenue": 0})
        entry["customers"] = int(entry["customers"]) + 1
        entry["revenue"] = entry["revenue"] + customer.monetary
    top_products = [
        {
            "product_id": str(item.product_id),
            "external_id": item.external_id,
            "name": item.name,
            "revenue": str(item.revenue),
        }
        for item in get_top_products(session, company_id, start_date, end_date, limit)
    ]
    stock_risk = [
        {
            "product_id": str(item.product.id),
            "external_id": item.product.external_id,
            "name": item.product.name,
            "status": item.status,
            "risk_level": item.risk_level,
            "days_of_cover": item.days_of_cover,
        }
        for item in risks
    ]
    return {
        "dashboard": {
            "total_revenue": str(dashboard.total_revenue),
            "units_sold": str(dashboard.units_sold),
            "sales_records": dashboard.sales_records,
            "active_customers": dashboard.active_customers,
            "average_sale_value": str(dashboard.average_sale_value),
            "top_products": top_products,
        },
        "rfm": {
            "total_customers": len(rfm),
            "segments": {
                key: {"customers": value["customers"], "revenue": str(value["revenue"])}
                for key, value in segments.items()
            },
        },
        "stock_risk": stock_risk,
    }
