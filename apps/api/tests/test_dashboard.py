from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.dashboard import get_revenue_series, get_summary, get_top_products


def create_session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def add_sale(
    session: Session,
    company: Company,
    dataset: Dataset,
    product: Product,
    customer: Customer,
    sale_date: date,
    quantity: str,
    revenue: str,
) -> None:
    session.add(
        Sale(
            company_id=company.id,
            dataset_id=dataset.id,
            product_id=product.id,
            customer_id=customer.id,
            sale_date=sale_date,
            quantity=Decimal(quantity),
            unit_price=Decimal("1"),
            revenue=Decimal(revenue),
        )
    )


def test_dashboard_aggregates_filters_and_tenant_scope() -> None:
    with create_session() as session:
        company_a = Company(name="Acme")
        company_b = Company(name="Beta")
        dataset_a = Dataset(company=company_a, name="a.csv", source_type="csv", status="completed")
        dataset_b = Dataset(company=company_b, name="b.csv", source_type="csv", status="completed")
        product_a = Product(company=company_a, external_id="P1", name="Mouse")
        product_b = Product(company=company_b, external_id="P1", name="Beta Mouse")
        customer_a = Customer(company=company_a, external_id="C1")
        customer_b = Customer(company=company_b, external_id="C1")
        session.add_all(
            [
                company_a,
                company_b,
                dataset_a,
                dataset_b,
                product_a,
                product_b,
                customer_a,
                customer_b,
            ]
        )
        session.flush()
        add_sale(session, company_a, dataset_a, product_a, customer_a, date(2026, 9, 1), "2", "200")
        add_sale(
            session, company_a, dataset_a, product_a, customer_a, date(2026, 10, 1), "3", "450"
        )
        add_sale(session, company_b, dataset_b, product_b, customer_b, date(2026, 9, 1), "9", "999")
        session.commit()

        september = get_summary(session, company_a.id, date(2026, 9, 1), date(2026, 9, 30))
        assert september.total_revenue == Decimal("200")
        assert september.units_sold == Decimal("2")
        assert september.sales_records == 1
        assert september.active_customers == 1
        assert september.average_sale_value == Decimal("200")

        series = get_revenue_series(session, company_a.id, None, None)
        assert [point.date for point in series] == [date(2026, 9, 1), date(2026, 10, 1)]
        assert [point.revenue for point in series] == [Decimal("200"), Decimal("450")]


def test_dashboard_top_products_and_empty_state() -> None:
    with create_session() as session:
        company = Company(name="Acme")
        empty_company = Company(name="Empty")
        dataset = Dataset(company=company, name="a.csv", source_type="csv", status="completed")
        mouse = Product(company=company, external_id="P1", name="Mouse")
        monitor = Product(company=company, external_id="P2", name="Monitor")
        customer = Customer(company=company, external_id="C1")
        session.add_all([company, empty_company, dataset, mouse, monitor, customer])
        session.flush()
        add_sale(session, company, dataset, mouse, customer, date(2026, 9, 1), "10", "100")
        add_sale(session, company, dataset, monitor, customer, date(2026, 9, 2), "1", "500")
        session.commit()

        assert get_top_products(session, company.id, None, None, 1)[0].name == "Monitor"
        empty = get_summary(session, empty_company.id, None, None)
        assert empty.total_revenue == Decimal("0")
        assert empty.sales_records == 0
        assert get_revenue_series(session, empty_company.id, None, None) == []
