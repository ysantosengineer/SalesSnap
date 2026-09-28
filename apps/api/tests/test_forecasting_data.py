from datetime import date
from decimal import Decimal

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import Company, Dataset, Product, Sale
from app.services.forecasting import build_continuous_demand_series, get_daily_product_demand


def test_daily_product_demand_aggregates_quantity_by_date_and_product() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company = Company(name="Forecast company")
        dataset = Dataset(company=company, name="Dataset", source_type="csv", status="completed")
        product = Product(company=company, external_id="P001", name="Widget")
        session.add_all([company, dataset, product])
        session.flush()
        session.add_all(
            [
                Sale(
                    company_id=company.id,
                    dataset_id=dataset.id,
                    product_id=product.id,
                    sale_date=date(2026, 9, 1),
                    quantity=Decimal("2"),
                    unit_price=Decimal("10"),
                    revenue=Decimal("20"),
                ),
                Sale(
                    company_id=company.id,
                    dataset_id=dataset.id,
                    product_id=product.id,
                    sale_date=date(2026, 9, 1),
                    quantity=Decimal("3"),
                    unit_price=Decimal("10"),
                    revenue=Decimal("30"),
                ),
            ]
        )
        session.commit()

        demand = get_daily_product_demand(session, company.id, product.id)

    assert demand.to_dict("records") == [{"date": date(2026, 9, 1), "quantity": Decimal("5.000")}]


def test_continuous_demand_series_fills_missing_days_with_zero() -> None:
    demand = pd.DataFrame({"date": [date(2026, 9, 1), date(2026, 9, 3)], "quantity": [5, 2]})

    series = build_continuous_demand_series(demand)

    assert series["date"].dt.date.tolist() == [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)]
    assert series["quantity"].tolist() == [5.0, 0.0, 2.0]
