from datetime import date
from decimal import Decimal

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.rfm import SEGMENTS, analyze_rfm, score, segment


def test_rfm_scores_are_stable_for_ties_and_small_populations() -> None:
    tied_scores = score(pd.Series([10, 10, 10]), ascending=True)
    assert tied_scores.tolist() == [4, 4, 4]

    single_score = score(pd.Series([10]), ascending=True)
    assert single_score.tolist() == [5]


def test_rfm_assigns_every_supported_segment() -> None:
    examples = {
        "Champions": (4, 4),
        "Loyal Customers": (3, 4),
        "Potential Loyalists": (4, 2),
        "New Customers": (5, 1),
        "At Risk": (2, 3),
        "Hibernating": (2, 2),
        "Need Attention": (3, 3),
    }

    assert set(examples) == set(SEGMENTS)
    assert {segment(*scores) for scores in examples.values()} == set(SEGMENTS)
    for expected_segment, scores in examples.items():
        assert segment(*scores) == expected_segment


def test_rfm_handles_a_single_customer_dataset() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company = Company(name="Single customer")
        dataset = Dataset(
            company=company,
            name="Single customer dataset",
            source_type="csv",
            status="completed",
        )
        product = Product(company=company, external_id="SKU-1", name="Widget")
        customer = Customer(company=company, external_id="C-1")
        session.add_all([company, dataset, product, customer])
        session.flush()
        session.add(
            Sale(
                company_id=company.id,
                dataset_id=dataset.id,
                product_id=product.id,
                customer_id=customer.id,
                sale_date=date(2026, 9, 30),
                quantity=Decimal("1"),
                unit_price=Decimal("25.00"),
                revenue=Decimal("25.00"),
            )
        )
        session.commit()

        customers, reference_date = analyze_rfm(session, company.id)

    assert reference_date == date(2026, 10, 1)
    assert len(customers) == 1
    assert customers[0].recency == 1
    assert customers[0].frequency == 1
    assert customers[0].monetary == Decimal("25.00")
    assert all(
        1 <= value <= 5 for value in customers[0].model_dump().values() if isinstance(value, int)
    )
