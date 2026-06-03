from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get the current user's dashboard summary",
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    service = DashboardService(db)
    return await service.get_summary(current_user.id)
