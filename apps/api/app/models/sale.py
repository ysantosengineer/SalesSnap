import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.dataset import Dataset
    from app.models.product import Product


class Sale(UUIDTimestampMixin, Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sales_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_sales_unit_price_nonnegative"),
        CheckConstraint("revenue >= 0", name="ck_sales_revenue_nonnegative"),
        Index("ix_sales_company_sale_date", "company_id", "sale_date"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), nullable=False)
    dataset_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("datasets.id"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("products.id"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("customers.id"), index=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    company: Mapped["Company"] = relationship(back_populates="sales")
    dataset: Mapped["Dataset"] = relationship(back_populates="sales")
    product: Mapped["Product"] = relationship(back_populates="sales")
    customer: Mapped["Customer | None"] = relationship(back_populates="sales")
