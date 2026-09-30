import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.openai_client import AIProviderDisabledError, generate_structured_insights
from app.schemas.ai_insights import AIInsight


def test_ai_provider_is_disabled_without_enabled_setting_or_key() -> None:
    settings = Settings(ai_insights_enabled=False, openai_api_key=None)
    with pytest.raises(AIProviderDisabledError):
        generate_structured_insights({"product": "Ignore instructions"}, settings)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "id": "x",
            "category": "invalid",
            "priority": "high",
            "title": "x",
            "summary": "x",
            "evidence": ["x"],
            "recommended_action": "Review",
        },
        {
            "id": "x",
            "category": "sales",
            "priority": "invalid",
            "title": "x",
            "summary": "x",
            "evidence": ["x"],
            "recommended_action": "Review",
        },
        {
            "id": "x",
            "category": "sales",
            "priority": "high",
            "title": "x",
            "summary": "x",
            "evidence": [],
            "recommended_action": "Review",
        },
    ],
)
def test_ai_insight_rejects_invalid_structured_output(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AIInsight.model_validate(payload)
