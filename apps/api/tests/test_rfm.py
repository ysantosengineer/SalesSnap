from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.rfm import analyze_rfm, segment


def test_rfm_uses_sales_records_and_tenant_population() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company_a, company_b = Company(name="A"), Company(name="B")
        dataset = Dataset(company=company_a, name="a", source_type="csv", status="completed")
        product = Product(company=company_a, external_id="P1", name="Product")
        customer = Customer(company=company_a, external_id="C1")
        session.add_all([company_a, company_b, dataset, product, customer])
        session.flush()
        session.add_all(
            [
                Sale(
                    company_id=company_a.id,
                    dataset_id=dataset.id,
                    product_id=product.id,
                    customer_id=customer.id,
                    sale_date=date(2026, 9, 28),
                    quantity=Decimal("10"),
                    unit_price=Decimal("20"),
                    revenue=Decimal("200"),
                ),
                Sale(
                    company_id=company_a.id,
                    dataset_id=dataset.id,
                    product_id=product.id,
                    customer_id=customer.id,
                    sale_date=date(2026, 9, 30),
                    quantity=Decimal("1"),
                    unit_price=Decimal("50"),
                    revenue=Decimal("50"),
                ),
            ]
        )
        session.commit()
        items, reference = analyze_rfm(session, company_a.id)
        assert reference == date(2026, 10, 1)
        assert items[0].frequency == 2
        assert items[0].monetary == Decimal("250")
        assert items[0].recency == 1
        assert items[0].segment in {
            "Champions",
            "Loyal Customers",
            "Potential Loyalists",
            "New Customers",
            "At Risk",
            "Hibernating",
            "Need Attention",
        }
        assert analyze_rfm(session, company_b.id) == ([], None)


def test_rfm_segment_precedence() -> None:
    assert segment(5, 5) == "Champions"
    assert segment(4, 2) == "Potential Loyalists"
    assert segment(1, 4) == "At Risk"
    assert segment(1, 1) == "Hibernating"
