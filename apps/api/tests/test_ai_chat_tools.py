import uuid

import pytest
from pydantic import ValidationError

from app.services.ai_chat_tools import TOOL_ARGUMENTS, execute_tool, tool_definitions


def test_tool_registry_exposes_only_read_only_tools() -> None:
    names = {item["name"] for item in tool_definitions()}
    assert names == set(TOOL_ARGUMENTS)
    assert "execute_sql" not in names
    assert "delete_sales" not in names


def test_tool_arguments_reject_invalid_forecast_horizon() -> None:
    with pytest.raises(ValueError, match="Unsupported forecast horizon"):
        execute_tool(
            None,
            uuid.uuid4(),
            "get_product_forecast",
            {"product_id": str(uuid.uuid4()), "horizon": 9999},
        )


def test_tool_arguments_reject_company_scope_from_model() -> None:
    with pytest.raises(ValidationError):
        TOOL_ARGUMENTS["get_sales_summary"].model_validate({"company_id": str(uuid.uuid4())})
