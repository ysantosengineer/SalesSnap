"""Persist bounded chat evidence and tool labels for conversation reloads."""

import sqlalchemy as sa

from alembic import op

revision = "20261002_01"
down_revision = "20260930_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_messages", sa.Column("evidence", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "chat_messages", sa.Column("tools_used", sa.JSON(), nullable=False, server_default="[]")
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "tools_used")
    op.drop_column("chat_messages", "evidence")
