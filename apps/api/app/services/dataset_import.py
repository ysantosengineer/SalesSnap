import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, Dataset, Product, Sale
from app.schemas.dataset_import import DatasetImportResponse
from app.services.csv_import import CsvStructuralError, parse_sales_csv


@dataclass(frozen=True)
class DatasetImportFailure(Exception):
    dataset_id: uuid.UUID
    message: str


def import_sales_dataset(
    session: Session, company_id: uuid.UUID, dataset_name: str, content: bytes
) -> DatasetImportResponse:
    """Persist a SalesSnap CSV V1 upload and all of its tenant-scoped sales records."""
    dataset = Dataset(
        company_id=company_id,
        name=dataset_name,
        source_type="csv",
        status="pending",
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    dataset.status = "processing"
    session.commit()

    try:
        parsed = parse_sales_csv(content)
    except CsvStructuralError as error:
        mark_dataset_failed(session, dataset.id)
        raise DatasetImportFailure(dataset.id, str(error)) from error

    try:
        products = {
            product.external_id: product
            for product in session.scalars(select(Product).where(Product.company_id == company_id))
        }
        customers = {
            customer.external_id: customer
            for customer in session.scalars(
                select(Customer).where(Customer.company_id == company_id)
            )
        }
        products_created = 0
        customers_created = 0
        for row in parsed.valid_rows:
            product = products.get(row.product_external_id)
            if product is None:
                product = Product(
                    company_id=company_id,
                    external_id=row.product_external_id,
                    name=row.product_name,
                )
                session.add(product)
                products[row.product_external_id] = product
                products_created += 1
            elif product.name != row.product_name:
                product.name = row.product_name

            customer = customers.get(row.customer_external_id)
            if customer is None:
                customer = Customer(company_id=company_id, external_id=row.customer_external_id)
                session.add(customer)
                customers[row.customer_external_id] = customer
                customers_created += 1

            session.flush()
            session.add(
                Sale(
                    company_id=company_id,
                    dataset_id=dataset.id,
                    product_id=product.id,
                    customer_id=customer.id,
                    sale_date=row.sale_date,
                    quantity=row.quantity,
                    unit_price=row.unit_price,
                    revenue=row.revenue,
                )
            )

        dataset.status = "completed"
        session.commit()
    except Exception:
        session.rollback()
        mark_dataset_failed(session, dataset.id)
        raise

    return DatasetImportResponse(
        dataset_id=dataset.id,
        status=dataset.status,
        rows_received=parsed.rows_received,
        rows_imported=len(parsed.valid_rows),
        rows_rejected=parsed.rows_received - len(parsed.valid_rows),
        products_created=products_created,
        customers_created=customers_created,
        sales_created=len(parsed.valid_rows),
        errors=parsed.errors,
    )


def mark_dataset_failed(session: Session, dataset_id: uuid.UUID) -> None:
    dataset = session.get(Dataset, dataset_id)
    if dataset is not None:
        dataset.status = "failed"
        session.commit()


def get_dataset(session: Session, company_id: uuid.UUID, dataset_id: uuid.UUID) -> Dataset | None:
    return session.scalar(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.company_id == company_id)
    )


def get_company_datasets(session: Session, company_id: uuid.UUID) -> list[Dataset]:
    return list(
        session.scalars(
            select(Dataset)
            .where(Dataset.company_id == company_id)
            .order_by(Dataset.created_at.desc())
        )
    )
