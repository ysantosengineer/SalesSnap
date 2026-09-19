"""add core tenant-aware domain schema

Revision ID: 20260919_01
Revises:
Create Date: 2026-09-19
"""

import sqlalchemy as sa

from alembic import op

revision = "20260919_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = sa.Uuid()
    op.create_table(
        "companies",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_table(
        "datasets",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_datasets_company_id", "datasets", ["company_id"])
    for table in ("products", "customers"):
        columns = [
            sa.Column("id", uuid_type, primary_key=True),
            sa.Column("company_id", uuid_type, sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("external_id", sa.String(length=255), nullable=False),
        ]
        if table == "products":
            columns.append(sa.Column("name", sa.String(length=255), nullable=False))
        columns.extend(
            [
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=False,
                ),
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=False,
                ),
                sa.UniqueConstraint(
                    "company_id", "external_id", name=f"uq_{table}_company_external_id"
                ),
            ]
        )
        op.create_table(table, *columns)
        op.create_index(f"ix_{table}_company_id", table, ["company_id"])
    op.create_table(
        "sales",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("company_id", uuid_type, sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("dataset_id", uuid_type, sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("product_id", uuid_type, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("customer_id", uuid_type, sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("revenue", sa.Numeric(16, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_sales_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_sales_unit_price_nonnegative"),
        sa.CheckConstraint("revenue >= 0", name="ck_sales_revenue_nonnegative"),
    )
    op.create_index("ix_sales_company_sale_date", "sales", ["company_id", "sale_date"])
    op.create_index("ix_sales_dataset_id", "sales", ["dataset_id"])
    op.create_index("ix_sales_product_id", "sales", ["product_id"])
    op.create_index("ix_sales_customer_id", "sales", ["customer_id"])


def downgrade() -> None:
    op.drop_table("sales")
    op.drop_table("customers")
    op.drop_table("products")
    op.drop_table("datasets")
    op.drop_table("companies")
