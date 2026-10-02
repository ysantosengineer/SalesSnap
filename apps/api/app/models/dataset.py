import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.sale import Sale


class Dataset(UUIDTimestampMixin, Base):
    __tablename__ = "datasets"
    __table_args__ = (Index("ix_datasets_company_created_at", "company_id", "created_at"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    company: Mapped["Company"] = relationship(back_populates="datasets")
    sales: Mapped[list["Sale"]] = relationship(back_populates="dataset")
