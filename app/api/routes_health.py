from fastapi import APIRouter

from app.config import APP_ENV, MODEL_NAME, is_openai_configured
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=MODEL_NAME,
        openai_configured=is_openai_configured(),
        environment=APP_ENV,
    )
