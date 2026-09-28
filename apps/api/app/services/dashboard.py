import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import Dataset, Product, Sale
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardSummary,
    LatestDataset,
    RevenueSeriesPoint,
    TopProduct,
)


def get_summary(
    session: Session, company_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> DashboardSummary:
    total_revenue, units_sold, sales_records, active_customers, average_sale_value = (
        session.execute(
            select(
                func.coalesce(func.sum(Sale.revenue), Decimal("0")),
                func.coalesce(func.sum(Sale.quantity), Decimal("0")),
                func.count(Sale.id),
                func.count(distinct(Sale.customer_id)),
                func.coalesce(func.avg(Sale.revenue), Decimal("0")),
            ).where(*sales_filters(company_id, start_date, end_date))
        ).one()
    )
    return DashboardSummary(
        total_revenue=total_revenue,
        units_sold=units_sold,
        sales_records=sales_records,
        active_customers=active_customers,
        average_sale_value=average_sale_value,
    )


def get_revenue_series(
    session: Session, company_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> list[RevenueSeriesPoint]:
    rows = session.execute(
        select(
            Sale.sale_date,
            func.sum(Sale.revenue),
            func.sum(Sale.quantity),
            func.count(Sale.id),
        )
        .where(*sales_filters(company_id, start_date, end_date))
        .group_by(Sale.sale_date)
        .order_by(Sale.sale_date.asc())
    )
    return [
        RevenueSeriesPoint(date=row[0], revenue=row[1], units_sold=row[2], sales_records=row[3])
        for row in rows
    ]


def get_top_products(
    session: Session,
    company_id: uuid.UUID,
    start_date: date | None,
    end_date: date | None,
    limit: int,
    order_by_units: bool = False,
) -> list[TopProduct]:
    revenue = func.sum(Sale.revenue).label("revenue")
    units_sold = func.sum(Sale.quantity).label("units_sold")
    sales_records = func.count(Sale.id).label("sales_records")
    order_metric = units_sold if order_by_units else revenue
    rows = session.execute(
        select(Product.id, Product.external_id, Product.name, revenue, units_sold, sales_records)
        .join(Sale, Sale.product_id == Product.id)
        .where(*sales_filters(company_id, start_date, end_date))
        .group_by(Product.id, Product.external_id, Product.name)
        .order_by(order_metric.desc(), Product.name.asc())
        .limit(limit)
    )
    return [
        TopProduct(
            product_id=row[0],
            external_id=row[1],
            name=row[2],
            revenue=row[3],
            units_sold=row[4],
            sales_records=row[5],
        )
        for row in rows
    ]


def get_overview(
    session: Session, company_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> DashboardOverview:
    series = get_revenue_series(session, company_id, start_date, end_date)
    latest_dataset = session.scalar(
        select(Dataset)
        .where(Dataset.company_id == company_id)
        .order_by(Dataset.created_at.desc())
        .limit(1)
    )
    return DashboardOverview(
        best_product_by_revenue=first_or_none(
            get_top_products(session, company_id, start_date, end_date, limit=1)
        ),
        best_product_by_units=first_or_none(
            get_top_products(
                session, company_id, start_date, end_date, limit=1, order_by_units=True
            )
        ),
        highest_revenue_day=max(series, key=lambda item: item.revenue) if series else None,
        latest_dataset=(
            LatestDataset(
                id=latest_dataset.id,
                name=latest_dataset.name,
                status=latest_dataset.status,
                created_at=latest_dataset.created_at,
            )
            if latest_dataset is not None
            else None
        ),
    )


def sales_filters(
    company_id: uuid.UUID, start_date: date | None, end_date: date | None
) -> tuple[object, ...]:
    filters: list[object] = [Sale.company_id == company_id]
    if start_date is not None:
        filters.append(Sale.sale_date >= start_date)
    if end_date is not None:
        filters.append(Sale.sale_date <= end_date)
    return tuple(filters)


def first_or_none(items: list[TopProduct]) -> TopProduct | None:
    return items[0] if items else None
