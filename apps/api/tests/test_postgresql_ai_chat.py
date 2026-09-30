import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.models import ChatMessage
from app.services.ai_chat import create_conversation, get_conversation, list_conversations
from app.services.auth import register_user


@pytest.mark.postgres
def test_ai_chat_migration_persistence_and_ownership_postgres() -> None:
    url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if url is None:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    directory = Path(__file__).parents[1]
    config = Config(str(directory / "alembic.ini"))
    config.set_main_option("script_location", str(directory / "alembic"))
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with Session(create_engine(url)) as session:
            owner = register_user(session, "Acme", "owner@acme.com", "secure-password")
            colleague = register_user(session, "Beta", "other@beta.com", "secure-password")
            conversation = create_conversation(
                session, owner.company_id, owner.id, "Revenue review"
            )
            session.add(
                ChatMessage(conversation_id=conversation.id, role="user", content="Revenue?")
            )
            session.add(
                ChatMessage(conversation_id=conversation.id, role="assistant", content="Available.")
            )
            session.commit()
            loaded = get_conversation(session, owner.company_id, owner.id, conversation.id)
            assert loaded is not None
            assert [message.role for message in loaded.messages] == ["user", "assistant"]
            assert (
                get_conversation(session, colleague.company_id, colleague.id, conversation.id)
                is None
            )
            assert [
                item.id for item in list_conversations(session, owner.company_id, owner.id)
            ] == [conversation.id]
    finally:
        command.downgrade(config, "base")
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
