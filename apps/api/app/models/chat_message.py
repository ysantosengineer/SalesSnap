import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.chat_conversation import ChatConversation


class ChatMessage(UUIDTimestampMixin, Base):
    """A persisted user or assistant message in a chat conversation."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
        Index(
            "ix_chat_messages_conversation_created",
            "conversation_id",
            "created_at",
            "id",
        ),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_conversations.id"), nullable=False, index=True
    )
    role: Mapped[Literal["user", "assistant"]] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    evidence: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)
    tools_used: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    conversation: Mapped["ChatConversation"] = relationship(back_populates="messages")
