import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.company import Company
    from app.models.user import User


class ChatConversation(UUIDTimestampMixin, Base):
    """A user-private, company-scoped AI chat conversation."""

    __tablename__ = "chat_conversations"
    __table_args__ = (
        Index(
            "ix_chat_conversations_company_user_updated",
            "company_id",
            "user_id",
            "updated_at",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New conversation")
    company: Mapped["Company"] = relationship()
    user: Mapped["User"] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="(ChatMessage.created_at, ChatMessage.id)",
    )
