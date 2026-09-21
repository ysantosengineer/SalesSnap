"""Small deterministic development seed for manual tenant-isolation checks."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Customer, Dataset, Product, Sale


def seed_development_data(session: Session) -> None:
    """Create two isolated example tenants; existing named tenants are preserved."""

    for company_name, product_external_id, customer_external_id in (
        ("Company A", "A-SKU-001", "A-CUSTOMER-001"),
        ("Company B", "B-SKU-001", "B-CUSTOMER-001"),
    ):
        if session.scalar(select(Company).where(Company.name == company_name)) is not None:
            continue
        company = Company(name=company_name)
        session.add(company)
        session.flush()
        dataset = Dataset(
            company_id=company.id,
            name="Development dataset",
            source_type="csv",
            status="completed",
        )
        product = Product(
            company_id=company.id,
            external_id=product_external_id,
            name="Development product",
        )
        customer = Customer(company_id=company.id, external_id=customer_external_id)
        session.add_all([dataset, product, customer])
        session.flush()
        session.add(
            Sale(
                company_id=company.id,
                dataset_id=dataset.id,
                product_id=product.id,
                customer_id=customer.id,
                sale_date=date(2026, 1, 1),
                quantity=Decimal("2"),
                unit_price=Decimal("10.00"),
                revenue=Decimal("20.00"),
            )
        )
    session.commit()
