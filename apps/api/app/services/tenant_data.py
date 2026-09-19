import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.dataset import Dataset
from app.models.product import Product
from app.models.sale import Sale


def get_product(session: Session, company_id: uuid.UUID, product_id: uuid.UUID) -> Product | None:
    return session.scalar(
        select(Product).where(Product.company_id == company_id, Product.id == product_id)
    )


def get_products(session: Session, company_id: uuid.UUID) -> list[Product]:
    return list(session.scalars(select(Product).where(Product.company_id == company_id)))


def get_customers(session: Session, company_id: uuid.UUID) -> list[Customer]:
    return list(session.scalars(select(Customer).where(Customer.company_id == company_id)))


def get_datasets(session: Session, company_id: uuid.UUID) -> list[Dataset]:
    return list(session.scalars(select(Dataset).where(Dataset.company_id == company_id)))


def get_sales(session: Session, company_id: uuid.UUID) -> list[Sale]:
    return list(session.scalars(select(Sale).where(Sale.company_id == company_id)))
