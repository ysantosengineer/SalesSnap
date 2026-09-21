from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.seed import seed_development_data
from app.db.session import Base
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.tenant_data import get_product, get_products


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


def test_persists_tenant_domain_relationships(session: Session) -> None:
    company = Company(name="Company A")
    session.add(company)
    session.flush()
    dataset = Dataset(company_id=company.id, name="January", source_type="csv", status="pending")
    product = Product(company_id=company.id, external_id="SKU-1", name="Widget")
    customer = Customer(company_id=company.id, external_id="CUST-1")
    session.add_all([dataset, product, customer])
    session.flush()
    sale = Sale(
        company_id=company.id,
        dataset_id=dataset.id,
        product_id=product.id,
        customer_id=customer.id,
        sale_date=date(2026, 1, 1),
        quantity=Decimal("2"),
        unit_price=Decimal("10.50"),
        revenue=Decimal("21.00"),
    )
    session.add(sale)
    session.commit()
    assert sale.product is product
    assert sale.customer is customer
    assert sale.dataset is dataset


def test_external_ids_are_unique_per_company(session: Session) -> None:
    first, second = Company(name="A"), Company(name="B")
    session.add_all([first, second])
    session.flush()
    session.add_all([
        Product(company_id=first.id, external_id="same", name="One"),
        Product(company_id=second.id, external_id="same", name="Two"),
    ])
    session.commit()
    session.add(Product(company_id=first.id, external_id="same", name="Duplicate"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_tenant_queries_do_not_cross_company_boundaries(session: Session) -> None:
    first, second = Company(name="A"), Company(name="B")
    session.add_all([first, second])
    session.flush()
    product_a = Product(company_id=first.id, external_id="A-1", name="A product")
    product_b = Product(company_id=second.id, external_id="B-1", name="B product")
    session.add_all([product_a, product_b])
    session.commit()
    assert get_products(session, first.id) == [product_a]
    assert get_product(session, first.id, product_b.id) is None


def test_development_seed_is_idempotent(session: Session) -> None:
    seed_development_data(session)
    seed_development_data(session)

    assert len(session.scalars(select(Company)).all()) == 2
    assert len(session.scalars(select(Sale)).all()) == 2
