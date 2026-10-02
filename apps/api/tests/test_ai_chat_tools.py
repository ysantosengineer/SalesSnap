import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.services.ai_chat_tools import TOOL_ARGUMENTS, execute_tool, tool_definitions


def test_tool_registry_exposes_only_read_only_tools() -> None:
    names = {item["name"] for item in tool_definitions()}
    assert names == set(TOOL_ARGUMENTS)
    assert "execute_sql" not in names
    assert "delete_sales" not in names


def test_tool_arguments_reject_invalid_forecast_horizon() -> None:
    with pytest.raises(ValidationError):
        execute_tool(
            None,
            uuid.uuid4(),
            "get_product_forecast",
            {"product_id": str(uuid.uuid4()), "horizon": 9999},
        )


def test_tool_arguments_reject_company_scope_from_model() -> None:
    with pytest.raises(ValidationError):
        TOOL_ARGUMENTS["get_sales_summary"].model_validate({"company_id": str(uuid.uuid4())})


@pytest.mark.parametrize("name", TOOL_ARGUMENTS)
@pytest.mark.parametrize("field", ["company_id", "user_id", "database_url"])
def test_all_tools_reject_model_selected_authority(name: str, field: str) -> None:
    args = {"product_id": str(uuid.uuid4())} if name == "get_product_forecast" else {}
    if name == "find_product":
        args["query"] = "P001"
    with pytest.raises(ValidationError):
        TOOL_ARGUMENTS[name].model_validate({**args, field: "untrusted"})


def test_provider_schemas_are_strict_compatible() -> None:
    for tool in tool_definitions():
        schema = tool["parameters"]
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])
        assert all("default" not in field for field in schema["properties"].values())


@pytest.mark.parametrize(
    "name,args",
    [
        ("get_sales_summary", {"start_date": "2026-10-02", "end_date": "2026-10-01"}),
        ("get_top_products", {"limit": 11}),
        ("get_customer_segments", {"segment": "Churn"}),
        ("get_sales_anomalies", {"limit": 11}),
        ("get_sales_anomalies", {"severity": "urgent"}),
        ("get_sales_anomalies", {"direction": "up"}),
        ("get_stock_risk", {"horizon": 999}),
        ("get_stock_risk", {"risk_level": "urgent"}),
        ("get_stock_risk", {"limit": 11}),
        ("find_product", {"query": "   "}),
    ],
)
def test_invalid_arguments_never_reach_handlers(monkeypatch, name, args) -> None:
    handler = Mock()
    monkeypatch.setitem(
        __import__("app.services.ai_chat_tools", fromlist=["_TOOL_HANDLERS"])._TOOL_HANDLERS,
        name,
        handler,
    )
    with pytest.raises(ValidationError):
        execute_tool(None, uuid.uuid4(), name, args)
    handler.assert_not_called()


@pytest.mark.parametrize(
    "tool,service", [("get_sales_summary", "get_summary"), ("get_top_products", "get_top_products")]
)
def test_dashboard_tools_reuse_tenant_and_dates(monkeypatch, tool, service) -> None:
    company = uuid.uuid4()
    metric = Mock()
    metric.model_dump.return_value = {"total_revenue": "10.50"}
    handler = Mock(return_value=metric if tool == "get_sales_summary" else [metric])
    monkeypatch.setattr(f"app.services.ai_chat_tools.{service}", handler)
    result = execute_tool(None, company, tool, {"start_date": "2026-10-01"})
    assert handler.call_args.args[:4] == (None, company, date(2026, 10, 1), None)
    assert result


def test_segments_include_real_revenue_without_customer_identifiers(monkeypatch) -> None:
    handler = Mock(
        return_value=(
            [
                SimpleNamespace(segment="At Risk", monetary=Decimal("12.50")),
                SimpleNamespace(segment="Champions", monetary=Decimal("90.00")),
            ],
            date(2026, 10, 1),
        )
    )
    monkeypatch.setattr("app.services.ai_chat_tools.analyze_rfm", handler)
    result = execute_tool(None, uuid.uuid4(), "get_customer_segments", {"segment": "At Risk"})
    assert result["segments"] == [{"segment": "At Risk", "customers": 1, "revenue": "12.50"}]


def test_forecast_uses_existing_service_and_removes_large_history(monkeypatch) -> None:
    company, product_id = uuid.uuid4(), uuid.uuid4()
    product = SimpleNamespace(id=product_id)
    lookup = Mock(return_value=product)
    forecast = Mock()
    forecast.model_dump.return_value = {"status": "insufficient_data"}
    handler = Mock(return_value=forecast)
    monkeypatch.setattr("app.services.ai_chat_tools.get_forecast_product", lookup)
    monkeypatch.setattr("app.services.ai_chat_tools.create_product_forecast", handler)
    execute_tool(
        None, company, "get_product_forecast", {"product_id": str(product_id), "horizon": 7}
    )
    lookup.assert_called_once_with(None, company, product_id)
    handler.assert_called_once_with(None, company, product, 7)
    forecast.model_dump.assert_called_once_with(mode="json", exclude={"history"})


def test_anomalies_apply_dates_severity_direction_and_limit(monkeypatch) -> None:
    company, product_id = uuid.uuid4(), uuid.uuid4()
    product = SimpleNamespace(id=product_id)

    def finding(day, severity="high", direction="spike"):
        item = Mock(date=date(2026, 10, day))
        item.model_dump.return_value = {
            "date": item.date.isoformat(),
            "severity": severity,
            "direction": direction,
        }
        return item

    handler = Mock(
        return_value=(
            [finding(1), finding(2), finding(3), finding(3, "low"), finding(3, direction="drop")],
            30,
        )
    )
    monkeypatch.setattr(
        "app.services.ai_chat_tools.get_forecast_product", Mock(return_value=product)
    )
    monkeypatch.setattr("app.services.ai_chat_tools.product_anomalies", handler)
    result = execute_tool(
        None,
        company,
        "get_sales_anomalies",
        {
            "product_id": str(product_id),
            "start_date": "2026-10-02",
            "end_date": "2026-10-03",
            "severity": "high",
            "direction": "spike",
            "limit": 1,
        },
    )
    assert result["total"] == 2
    assert result["anomalies"] == [{"date": "2026-10-03", "severity": "high", "direction": "spike"}]
    assert handler.call_args.args[:3] == (None, company, product)


def test_stock_risk_filters_and_ranks_before_limiting(monkeypatch) -> None:
    def risk(name, level):
        item = Mock()
        item.model_dump.return_value = {"product": {"name": name}, "risk_level": level}
        return item

    handler = Mock(return_value=([risk("A", "safe"), risk("Z", "critical")], 2))
    monkeypatch.setattr("app.services.ai_chat_tools.list_stock_risk_results", handler)
    company = uuid.uuid4()
    result = execute_tool(None, company, "get_stock_risk", {"risk_level": "critical", "limit": 1})
    assert result["results"][0]["product"]["name"] == "Z"
    handler.assert_called_once_with(None, company, 30)


@pytest.mark.parametrize("tool", ["get_product_forecast", "get_sales_anomalies", "get_stock_risk"])
def test_foreign_product_never_reaches_analytics(monkeypatch, tool) -> None:
    lookup = Mock(return_value=None)
    monkeypatch.setattr("app.services.ai_chat_tools.get_forecast_product", lookup)
    handler = Mock(side_effect=AssertionError("Foreign product reached analytics"))
    for service in ["create_product_forecast", "product_anomalies", "build_stock_risk_result"]:
        monkeypatch.setattr(f"app.services.ai_chat_tools.{service}", handler)
    execute_tool(None, uuid.uuid4(), tool, {"product_id": str(uuid.uuid4())})
    handler.assert_not_called()
