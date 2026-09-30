import json
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.prompts.ai_insights import AI_INSIGHTS_SYSTEM_PROMPT
from app.schemas.ai_insights import AIInsightsResponse


class AIProviderDisabledError(Exception):
    pass


class AIProviderUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class ChatToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ChatProviderResponse:
    text: str
    tool_calls: list[ChatToolCall]


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


def generate_chat_response(
    input_items: list[dict[str, Any]], tools: list[dict[str, Any]], settings: Settings
) -> ChatProviderResponse:
    """Invoke the centralized OpenAI provider without giving it database access."""
    if not settings.ai_insights_enabled or not settings.openai_api_key:
        raise AIProviderDisabledError
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openai_api_key, timeout=settings.ai_insights_timeout_seconds
        )
        response = client.responses.create(
            model=settings.openai_model,
            input=input_items,
            tools=tools,
            max_output_tokens=settings.ai_chat_max_output_tokens,
            store=False,
        )
        calls = []
        for item in response.output:
            if item.type == "function_call":
                calls.append(
                    ChatToolCall(
                        call_id=item.call_id,
                        name=item.name,
                        arguments=json.loads(item.arguments),
                    )
                )
        return ChatProviderResponse(text=response.output_text or "", tool_calls=calls)
    except AIProviderDisabledError:
        raise
    except Exception as error:
        raise AIProviderUnavailableError from error
