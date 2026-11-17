from enum import StrEnum

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, string_enum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    factory_id: Mapped[int | None] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))


class ChatMessage(CreatedAtMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_conversation_id_id", "conversation_id", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(string_enum(MessageRole, "message_role"))
    content: Mapped[str] = mapped_column(Text)
