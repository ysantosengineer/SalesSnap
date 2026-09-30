from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.openai_client import generate_structured_insights
from app.schemas.ai_insights import AIInsightsResponse
from app.services.ai_insight_context import build_ai_insight_context


def generate_ai_insights(
    session: Session, company_id, start_date=None, end_date=None
) -> AIInsightsResponse:
    context = build_ai_insight_context(session, company_id, start_date, end_date)
    response = generate_structured_insights(context, get_settings())
    allowed_products = {
        item["product_id"]
        for section in (context.get("dashboard", {}).get("top_products", []), context["stock_risk"])
        for item in section
    }
    for insight in response.insights:
        if insight.related_product_id and str(insight.related_product_id) not in allowed_products:
            raise ValueError("AI response references an unknown product")
    return response.model_copy(update={"generated_at": datetime.now(UTC)})
