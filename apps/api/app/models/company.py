from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.dataset import Dataset
    from app.models.product import Product
    from app.models.sale import Sale


class Company(UUIDTimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="company")
    products: Mapped[list["Product"]] = relationship(back_populates="company")
    customers: Mapped[list["Customer"]] = relationship(back_populates="company")
    sales: Mapped[list["Sale"]] = relationship(back_populates="company")
