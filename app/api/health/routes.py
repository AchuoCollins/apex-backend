from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.config import settings
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str
    database: str


@router.get("", response_model=HealthResponse, summary="Service health check")
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
    )
