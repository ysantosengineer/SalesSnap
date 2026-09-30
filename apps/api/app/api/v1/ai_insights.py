from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db_session
from app.integrations.openai_client import AIProviderDisabledError, AIProviderUnavailableError
from app.models import User
from app.schemas.ai_insights import AIInsightsRequest, AIInsightsResponse
from app.services.ai_insights import generate_ai_insights

router = APIRouter(prefix="/analytics/ai-insights", tags=["analytics"])


@router.post("/generate", response_model=AIInsightsResponse)
def generate(
    request: AIInsightsRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AIInsightsResponse:
    if request.start_date and request.end_date and request.start_date > request.end_date:
        raise HTTPException(422, "start_date must be before end_date")
    try:
        return generate_ai_insights(
            session, current_user.company_id, request.start_date, request.end_date
        )
    except AIProviderDisabledError as error:
        raise HTTPException(503, "AI insights are not configured for this environment.") from error
    except AIProviderUnavailableError as error:
        raise HTTPException(503, "AI insights are temporarily unavailable.") from error
    except ValueError as error:
        raise HTTPException(502, "AI provider returned an invalid response.") from error
