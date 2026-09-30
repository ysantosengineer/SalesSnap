import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=255)


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatEvidence(BaseModel):
    source: str
    label: str
    value: str


class ChatMessageRead(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationRead(ConversationSummary):
    messages: list[ChatMessageRead]


class AIChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    message: str
    evidence: list[ChatEvidence] = []
    tools_used: list[str] = []
    created_at: datetime
