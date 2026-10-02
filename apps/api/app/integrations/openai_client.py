import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.prompts.ai_insights import AI_INSIGHTS_SYSTEM_PROMPT
from app.schemas.ai_insights import AIInsightsResponse

logger = logging.getLogger("sales_snap.ai")


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
    output_items: list[dict[str, Any]] = field(default_factory=list)


@lru_cache(maxsize=1)
def _client(api_key: str, timeout: int):
    """One client factory shared by Insights and Chat; credentials never enter prompts."""
    from openai import OpenAI

    return OpenAI(api_key=api_key, timeout=timeout)


def generate_structured_insights(
    context: dict[str, object], settings: Settings
) -> AIInsightsResponse:
    if not settings.ai_insights_enabled or not settings.openai_api_key:
        raise AIProviderDisabledError
    started_at = perf_counter()
    logger.info(
        "ai_provider_called", extra={"operation": "insights", "model": settings.openai_model}
    )
    try:
        client = _client(settings.openai_api_key, settings.ai_insights_timeout_seconds)
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
        logger.info(
            "ai_provider_completed",
            extra={
                "operation": "insights",
                "model": settings.openai_model,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )
        return response.output_parsed
    except AIProviderDisabledError:
        raise
    except Exception as error:
        logger.warning(
            "ai_provider_failed",
            extra={
                "operation": "insights",
                "model": settings.openai_model,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "error_type": type(error).__name__,
            },
        )
        raise AIProviderUnavailableError from error


def generate_chat_response(
    input_items: list[dict[str, Any]], tools: list[dict[str, Any]], settings: Settings
) -> ChatProviderResponse:
    """Invoke the centralized OpenAI provider without giving it database access."""
    if not settings.ai_insights_enabled or not settings.openai_api_key:
        raise AIProviderDisabledError
    started_at = perf_counter()
    logger.info("ai_provider_called", extra={"operation": "chat", "model": settings.openai_model})
    try:
        client = _client(settings.openai_api_key, settings.ai_insights_timeout_seconds)
        response = client.responses.create(
            model=settings.openai_model,
            input=input_items,
            tools=tools,
            max_output_tokens=settings.ai_chat_max_output_tokens,
            store=False,
            include=["reasoning.encrypted_content"],
        )
        if response.status != "completed":
            raise AIProviderUnavailableError
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
        result = ChatProviderResponse(
            text=response.output_text or "",
            tool_calls=calls,
            output_items=[
                item.model_dump(mode="json", exclude_none=True) for item in response.output
            ],
        )
        logger.info(
            "ai_provider_completed",
            extra={
                "operation": "chat",
                "model": settings.openai_model,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "tool_calls": len(result.tool_calls),
            },
        )
        return result
    except AIProviderDisabledError:
        raise
    except Exception as error:
        logger.warning(
            "ai_provider_failed",
            extra={
                "operation": "chat",
                "model": settings.openai_model,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "error_type": type(error).__name__,
            },
        )
        raise AIProviderUnavailableError from error
