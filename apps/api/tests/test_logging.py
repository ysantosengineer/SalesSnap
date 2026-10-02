import json
import logging

from app.core.logging import JsonFormatter, request_id_context


def test_structured_logging_includes_safe_operational_fields() -> None:
    formatter = JsonFormatter()
    token = request_id_context.set("request-123")
    try:
        record = logging.LogRecord(
            "sales_snap.requests",
            logging.INFO,
            __file__,
            1,
            "request_completed",
            (),
            None,
        )
        record.path = "/api/v1/health"
        record.status_code = 200
        record.duration_ms = 1.5
        payload = json.loads(formatter.format(record))
    finally:
        request_id_context.reset(token)

    assert payload["event"] == "request_completed"
    assert payload["request_id"] == "request-123"
    assert payload["path"] == "/api/v1/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 1.5
    assert "authorization" not in payload
