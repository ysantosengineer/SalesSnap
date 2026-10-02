from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.config import Settings
from app.integrations import openai_client as provider


def test_provider_preserves_calls_and_reasoning_for_next_request(monkeypatch):
    call = Mock(type="function_call", call_id="c1", arguments='{"query":"P001","limit":5}')
    call.name = "find_product"
    call.model_dump.return_value = {
        "type": "function_call",
        "call_id": "c1",
        "name": "find_product",
        "arguments": call.arguments,
    }
    reasoning = Mock(type="reasoning")
    reasoning.model_dump.return_value = {"type": "reasoning", "encrypted_content": "opaque"}
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        status="completed", output=[reasoning, call], output_text=""
    )
    factory = Mock(return_value=client)
    monkeypatch.setattr(provider, "_client", factory)
    settings = Settings(ai_insights_enabled=True, openai_api_key="provider-only-test-value")
    result = provider.generate_chat_response([{"role": "user", "content": "P001?"}], [], settings)
    assert result.tool_calls[0].name == "find_product"
    assert result.output_items == [reasoning.model_dump.return_value, call.model_dump.return_value]
    request = client.responses.create.call_args.kwargs
    assert request["store"] is False
    assert request["max_output_tokens"] == 800
    assert "provider-only-test-value" not in str(request)


@pytest.mark.parametrize("status", ["incomplete", "failed", "cancelled"])
def test_provider_rejects_noncompleted_response(monkeypatch, status):
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(status=status)
    monkeypatch.setattr(provider, "_client", Mock(return_value=client))
    with pytest.raises(provider.AIProviderUnavailableError):
        provider.generate_chat_response(
            [], [], Settings(ai_insights_enabled=True, openai_api_key="test")
        )


def test_disabled_provider_never_constructs_client(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(provider, "_client", factory)
    with pytest.raises(provider.AIProviderDisabledError):
        provider.generate_chat_response([], [], Settings(ai_insights_enabled=False))
    factory.assert_not_called()


def test_provider_masks_transport_failures(monkeypatch):
    factory = Mock(side_effect=TimeoutError("private transport details"))
    monkeypatch.setattr(provider, "_client", factory)
    with pytest.raises(provider.AIProviderUnavailableError) as failure:
        provider.generate_chat_response(
            [], [], Settings(ai_insights_enabled=True, openai_api_key="test")
        )
    assert "private" not in str(failure.value)
