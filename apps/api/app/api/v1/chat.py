import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.db.session import get_db_session
from app.integrations.openai_client import AIProviderDisabledError, AIProviderUnavailableError
from app.models import User
from app.schemas.ai_chat import (
    AIChatResponse,
    ChatMessageRead,
    ConversationCreate,
    ConversationRead,
    ConversationSummary,
    MessageCreate,
)
from app.services.ai_chat import (
    create_conversation,
    get_conversation,
    list_conversations,
    send_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/conversations", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED
)
def create_chat_conversation(
    payload: ConversationCreate,
    session: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ConversationSummary:
    return ConversationSummary.model_validate(
        create_conversation(session, user.company_id, user.id, payload.title), from_attributes=True
    )


@router.get("/conversations", response_model=list[ConversationSummary])
def get_chat_conversations(
    session: Session = Depends(get_db_session), user: User = Depends(get_current_user)
) -> list[ConversationSummary]:
    return [
        ConversationSummary.model_validate(item, from_attributes=True)
        for item in list_conversations(session, user.company_id, user.id)
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def get_chat_conversation(
    conversation_id: uuid.UUID,
    session: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ConversationRead:
    conversation = _conversation_or_404(session, user, conversation_id)
    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ChatMessageRead.model_validate(item, from_attributes=True)
            for item in conversation.messages
        ],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=AIChatResponse)
def post_chat_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    request: Request,
    session: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> AIChatResponse:
    enforce_rate_limit(
        request,
        "ai_chat",
        str(user.id),
        get_settings().rate_limit_ai_chat_per_minute,
    )
    conversation = _conversation_or_404(session, user, conversation_id)
    try:
        return send_message(session, conversation, payload.message)
    except AIProviderDisabledError as error:
        raise HTTPException(
            status_code=503, detail="AI Chat is not configured for this environment."
        ) from error
    except AIProviderUnavailableError as error:
        raise HTTPException(
            status_code=503, detail="I couldn't analyze your data right now."
        ) from error


def _conversation_or_404(session: Session, user: User, conversation_id: uuid.UUID):
    conversation = get_conversation(session, user.company_id, user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
