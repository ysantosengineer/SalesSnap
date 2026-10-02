"""Conversation persistence and bounded read-only AI chat orchestration."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.openai_client import AIProviderUnavailableError, generate_chat_response
from app.models import ChatConversation, ChatMessage
from app.prompts.ai_chat import AI_CHAT_SYSTEM_PROMPT
from app.schemas.ai_chat import AIChatResponse, ChatEvidence
from app.services.ai_chat_tools import execute_tool, tool_definitions


class AIChatToolError(AIProviderUnavailableError):
    """The provider requested an invalid tool, arguments, or exceeded its budget."""


def create_conversation(
    session: Session, company_id: uuid.UUID, user_id: uuid.UUID, title: str
) -> ChatConversation:
    conversation = ChatConversation(company_id=company_id, user_id=user_id, title=title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def list_conversations(
    session: Session, company_id: uuid.UUID, user_id: uuid.UUID
) -> list[ChatConversation]:
    return list(
        session.scalars(
            select(ChatConversation)
            .where(ChatConversation.company_id == company_id, ChatConversation.user_id == user_id)
            .order_by(ChatConversation.updated_at.desc())
        )
    )


def get_conversation(
    session: Session, company_id: uuid.UUID, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> ChatConversation | None:
    return session.scalar(
        select(ChatConversation).where(
            ChatConversation.id == conversation_id,
            ChatConversation.company_id == company_id,
            ChatConversation.user_id == user_id,
        )
    )


def send_message(session: Session, conversation: ChatConversation, content: str) -> AIChatResponse:
    user_message = ChatMessage(
        conversation_id=conversation.id, role="user", content=content, created_at=datetime.now(UTC)
    )
    session.add(user_message)
    if conversation.title == "New conversation":
        conversation.title = " ".join(content.split())[:80]
    conversation.updated_at = datetime.now(UTC)
    session.commit()
    settings = get_settings()
    history = list(
        session.scalars(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(settings.ai_chat_history_messages)
        )
    )
    inputs: list[dict[str, Any]] = [{"role": "system", "content": AI_CHAT_SYSTEM_PROMPT}]
    inputs.extend({"role": item.role, "content": item.content} for item in reversed(history))
    tools_used: list[str] = []
    evidence: list[ChatEvidence] = []
    call_count = 0
    for _ in range(settings.ai_chat_max_tool_calls + 1):
        response = generate_chat_response(inputs, tool_definitions(), settings)
        if not response.tool_calls:
            if not response.text.strip():
                raise AIProviderUnavailableError
            assistant = ChatMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=response.text,
                evidence=[item.model_dump() for item in evidence],
                tools_used=tools_used,
                created_at=datetime.now(UTC),
            )
            conversation.updated_at = datetime.now(UTC)
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            return AIChatResponse(
                conversation_id=conversation.id,
                message_id=assistant.id,
                message=assistant.content,
                evidence=evidence,
                tools_used=tools_used,
                created_at=assistant.created_at,
            )
        if call_count + len(response.tool_calls) > settings.ai_chat_max_tool_calls:
            raise AIChatToolError("Tool call limit reached")
        # Replay the provider's calls (and opaque reasoning items) before their outputs.
        inputs.extend(
            response.output_items
            or [
                {
                    "type": "function_call",
                    "call_id": call.call_id,
                    "name": call.name,
                    "arguments": json.dumps(call.arguments),
                }
                for call in response.tool_calls
            ]
        )
        for call in response.tool_calls:
            try:
                result = execute_tool(session, conversation.company_id, call.name, call.arguments)
            except ValueError as error:
                raise AIChatToolError("Invalid tool request") from error
            call_count += 1
            if call.name not in tools_used:
                tools_used.append(call.name)
            evidence.extend(_tool_evidence(call.name, result))
            inputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, default=str),
                }
            )
    raise AIProviderUnavailableError


def _tool_evidence(source: str, result: dict[str, Any]) -> list[ChatEvidence]:
    """Expose actual returned values, not LLM-invented citations or full tool dumps."""
    facts: list[ChatEvidence] = []

    def visit(value: Any, path: str) -> None:
        if len(facts) >= 50:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if key not in {"id", "product_id", "customer_id"}:
                    visit(item, f"{path}.{key}" if path else key)
        elif isinstance(value, list):
            if not value:
                facts.append(ChatEvidence(source=source, label=path, value="No results"))
            for index, item in enumerate(value[:10]):
                visit(item, f"{path}[{index + 1}]")
        else:
            facts.append(
                ChatEvidence(
                    source=source,
                    label=path,
                    value=("Not available" if value is None else str(value))[:500],
                )
            )

    visit(result, "")
    return facts
