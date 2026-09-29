"""add inventory snapshots

Revision ID: 20260929_01
Revises: 20260921_01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260929_01"
down_revision = "20260921_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False),
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
        sa.CheckConstraint(
            "quantity_on_hand >= 0",
            name="ck_inventory_snapshots_quantity_nonnegative",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "product_id",
            "snapshot_date",
            name="uq_inventory_snapshots_company_product_date",
        ),
    )
    op.create_index("ix_inventory_snapshots_company_id", "inventory_snapshots", ["company_id"])
    op.create_index("ix_inventory_snapshots_product_id", "inventory_snapshots", ["product_id"])


def downgrade() -> None:
    op.drop_table("inventory_snapshots")
