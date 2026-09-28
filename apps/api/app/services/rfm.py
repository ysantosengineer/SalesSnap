import math
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, Sale
from app.schemas.rfm import RfmCustomer

SEGMENTS = (
    "Champions",
    "Loyal Customers",
    "Potential Loyalists",
    "New Customers",
    "At Risk",
    "Hibernating",
    "Need Attention",
)


def aggregate_customer_sales(
    session: Session, company_id: uuid.UUID, start_date: date | None, end_date: date | None
):
    filters = [Sale.company_id == company_id]
    if start_date:
        filters.append(Sale.sale_date >= start_date)
    if end_date:
        filters.append(Sale.sale_date <= end_date)
    return list(
        session.execute(
            select(
                Customer.id,
                Customer.external_id,
                func.max(Sale.sale_date),
                func.count(Sale.id),
                func.sum(Sale.revenue),
            )
            .join(Sale, Sale.customer_id == Customer.id)
            .where(*filters)
            .group_by(Customer.id, Customer.external_id)
        )
    )


def analyze_rfm(
    session: Session,
    company_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    reference_date: date | None = None,
) -> tuple[list[RfmCustomer], date | None]:
    rows = aggregate_customer_sales(session, company_id, start_date, end_date)
    if not rows:
        return [], None
    latest = max(row[2] for row in rows)
    reference = reference_date or (
        (end_date + timedelta(days=1)) if end_date else latest + timedelta(days=1)
    )
    if reference <= latest:
        raise ValueError("reference_date must be after the latest sale date")
    frame = pd.DataFrame(rows, columns=["id", "external_id", "last_sale", "frequency", "monetary"])
    frame["recency"] = frame["last_sale"].map(lambda value: (reference - value).days)
    frame["r_score"] = score(frame["recency"], ascending=False)
    frame["f_score"] = score(frame["frequency"], ascending=True)
    frame["m_score"] = score(frame["monetary"], ascending=True)
    frame["fm_score"] = ((frame["f_score"] + frame["m_score"]) / 2).round().astype(int)
    frame["segment"] = frame.apply(lambda item: segment(item.r_score, item.fm_score), axis=1)
    return [
        RfmCustomer(
            customer_id=row.id,
            external_id=row.external_id,
            recency=int(row.recency),
            frequency=int(row.frequency),
            monetary=Decimal(row.monetary),
            r_score=int(row.r_score),
            f_score=int(row.f_score),
            m_score=int(row.m_score),
            fm_score=int(row.fm_score),
            segment=row.segment,
        )
        for row in frame.itertuples()
    ], reference


def score(values: pd.Series, ascending: bool) -> pd.Series:
    percentiles = values.rank(method="average", pct=True, ascending=ascending)
    return percentiles.map(lambda value: max(1, min(5, math.ceil(value * 5)))).astype(int)


def segment(r_score: int, fm_score: int) -> str:
    if r_score >= 4 and fm_score >= 4:
        return "Champions"
    if r_score >= 3 and fm_score >= 4:
        return "Loyal Customers"
    if r_score >= 4 and 2 <= fm_score <= 3:
        return "Potential Loyalists"
    if r_score == 5 and fm_score <= 2:
        return "New Customers"
    if r_score <= 2 and fm_score >= 3:
        return "At Risk"
    if r_score <= 2 and fm_score <= 2:
        return "Hibernating"
    return "Need Attention"
