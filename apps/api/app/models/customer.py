import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.sale import Sale


class Customer(UUIDTimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("company_id", "external_id", name="uq_customers_company_external_id"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped["Company"] = relationship(back_populates="customers")
    sales: Mapped[list["Sale"]] = relationship(back_populates="customer")
