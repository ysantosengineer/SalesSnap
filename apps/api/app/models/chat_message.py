import uuid
from typing import TYPE_CHECKING, Literal

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.chat_conversation import ChatConversation


class ChatMessage(UUIDTimestampMixin, Base):
    """A persisted user or assistant message in a chat conversation."""

    __tablename__ = "chat_messages"
    __table_args__ = (CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),)

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_conversations.id"), nullable=False, index=True
    )
    role: Mapped[Literal["user", "assistant"]] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    conversation: Mapped["ChatConversation"] = relationship(back_populates="messages")
