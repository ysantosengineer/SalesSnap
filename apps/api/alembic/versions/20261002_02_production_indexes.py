"""Add composite indexes for production query paths."""

from alembic import op

revision = "20261002_02"
down_revision = "20261002_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_datasets_company_created_at", "datasets", ["company_id", "created_at"]
    )
    op.create_index(
        "ix_sales_company_product_date",
        "sales",
        ["company_id", "product_id", "sale_date"],
    )
    op.create_index(
        "ix_sales_company_customer_date",
        "sales",
        ["company_id", "customer_id", "sale_date"],
    )
    op.create_index(
        "ix_chat_conversations_company_user_updated",
        "chat_conversations",
        ["company_id", "user_id", "updated_at"],
    )
    op.create_index(
        "ix_chat_messages_conversation_created",
        "chat_messages",
        ["conversation_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_conversation_created", table_name="chat_messages")
    op.drop_index(
        "ix_chat_conversations_company_user_updated", table_name="chat_conversations"
    )
    op.drop_index("ix_sales_company_customer_date", table_name="sales")
    op.drop_index("ix_sales_company_product_date", table_name="sales")
    op.drop_index("ix_datasets_company_created_at", table_name="datasets")
