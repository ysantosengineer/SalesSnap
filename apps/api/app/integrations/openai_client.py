import json

from app.core.config import Settings
from app.prompts.ai_insights import AI_INSIGHTS_SYSTEM_PROMPT
from app.schemas.ai_insights import AIInsightsResponse


class AIProviderDisabledError(Exception):
    pass


class AIProviderUnavailableError(Exception):
    pass


def generate_structured_insights(
    context: dict[str, object], settings: Settings
) -> AIInsightsResponse:
    if not settings.ai_insights_enabled or not settings.openai_api_key:
        raise AIProviderDisabledError
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openai_api_key, timeout=settings.ai_insights_timeout_seconds
        )
        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": AI_INSIGHTS_SYSTEM_PROMPT},
                {"role": "user", "content": f"DATA\n{json.dumps(context, default=str)}\nEND DATA"},
            ],
            text_format=AIInsightsResponse,
        )
        if response.output_parsed is None:
            raise AIProviderUnavailableError
        return response.output_parsed
    except AIProviderDisabledError:
        raise
    except Exception as error:
        raise AIProviderUnavailableError from error
