import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.dataset_import import DatasetImportFailure, get_dataset, import_sales_dataset
from app.services import dataset_import

CSV_HEADER = b"date,customer_id,product_id,product_name,quantity,unit_price\n"


def create_session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_import_persists_tenant_data_and_reports_partial_rejections() -> None:
    with create_session() as session:
        company = Company(name="Acme")
        session.add(company)
        session.commit()
        content = (
            CSV_HEADER
            + b"2026-09-01,C001,P001,Mouse,2,149.90\n"
            + b"2026-99-99,C002,P002,Monitor,1,1299.90\n"
        )

        result = import_sales_dataset(session, company.id, "sales.csv", content)

        assert result.status == "completed"
        assert result.rows_received == 2
        assert result.rows_imported == 1
        assert result.rows_rejected == 1
        assert result.products_created == 1
        assert result.customers_created == 1
        assert result.sales_created == 1
        assert session.get(Dataset, result.dataset_id).status == "completed"
        sale = session.query(Sale).one()
        assert sale.company_id == company.id
        assert sale.dataset_id == result.dataset_id
        assert sale.revenue == Decimal("299.80")


def test_import_reuses_tenant_identities_and_updates_product_name() -> None:
    with create_session() as session:
        company = Company(name="Acme")
        product = Product(company=company, external_id="P001", name="Old mouse")
        customer = Customer(company=company, external_id="C001")
        session.add_all([product, customer])
        session.commit()

        result = import_sales_dataset(
            session,
            company.id,
            "sales.csv",
            CSV_HEADER + b"2026-09-01,C001,P001,New mouse,1,10.00\n",
        )

        assert result.products_created == 0
        assert result.customers_created == 0
        assert session.get(Product, product.id).name == "New mouse"
        assert session.query(Sale).one().product_id == product.id
        assert session.query(Sale).one().customer_id == customer.id


def test_structural_failure_marks_dataset_failed_without_sales() -> None:
    with create_session() as session:
        company = Company(name="Acme")
        session.add(company)
        session.commit()

        with pytest.raises(DatasetImportFailure) as failure:
            import_sales_dataset(
                session, company.id, "invalid.csv", b"date,customer_id\n2026-09-01,C001\n"
            )

        assert session.get(Dataset, failure.value.dataset_id).status == "failed"
        assert session.query(Sale).count() == 0


def test_dataset_lookup_is_scoped_to_company() -> None:
    with create_session() as session:
        company_a = Company(name="Acme")
        company_b = Company(name="Beta")
        session.add_all([company_a, company_b])
        session.commit()
        result = import_sales_dataset(
            session,
            company_a.id,
            "sales.csv",
            CSV_HEADER + b"2026-09-01,C001,P001,Mouse,1,10\n",
        )

        assert get_dataset(session, company_a.id, result.dataset_id) is not None
        assert get_dataset(session, company_b.id, result.dataset_id) is None
        assert get_dataset(session, company_b.id, uuid.uuid4()) is None


def test_unexpected_persistence_failure_marks_dataset_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with create_session() as session:
        company = Company(name="Acme")
        session.add(company)
        session.commit()

        class BrokenSale:
            def __init__(self, **_: object) -> None:
                raise RuntimeError("simulated persistence failure")

        monkeypatch.setattr(dataset_import, "Sale", BrokenSale)
        with pytest.raises(RuntimeError, match="simulated persistence failure"):
            import_sales_dataset(
                session,
                company.id,
                "sales.csv",
                CSV_HEADER + b"2026-09-01,C001,P001,Mouse,1,10\n",
            )

        assert session.query(Dataset).one().status == "failed"
        assert session.query(Sale).count() == 0
