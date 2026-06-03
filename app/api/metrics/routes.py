from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.metrics_service import MetricsService
from app.schemas.metrics import MetricsCreate, MetricsUpdate, MetricsResponse, MetricsList

router = APIRouter(prefix="/metrics", tags=["Body Metrics"])


@router.post(
    "",
    response_model=MetricsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new set of body measurements",
)
async def create_metrics(
    data: MetricsCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse:
    service = MetricsService(db)
    return await service.create(current_user.id, data)


@router.get(
    "",
    response_model=MetricsList,
    summary="Get all body metrics history for current user",
)
async def get_metrics(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricsList:
    service = MetricsService(db)
    return await service.get_list(current_user.id, skip=skip, limit=limit)


@router.get(
    "/latest",
    response_model=MetricsResponse | None,
    summary="Get the most recent body metrics snapshot",
)
async def get_latest_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse | None:
    service = MetricsService(db)
    return await service.get_latest(current_user.id)


@router.get(
    "/{metrics_id}",
    response_model=MetricsResponse,
    summary="Get a specific metrics snapshot by ID",
)
async def get_metrics_by_id(
    metrics_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse:
    service = MetricsService(db)
    return await service.get_by_id(metrics_id, current_user.id)


@router.put(
    "/{metrics_id}",
    response_model=MetricsResponse,
    summary="Update a metrics snapshot",
)
async def update_metrics(
    metrics_id: int,
    data: MetricsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse:
    service = MetricsService(db)
    return await service.update(metrics_id, current_user.id, data)


@router.delete(
    "/{metrics_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a metrics snapshot",
)
async def delete_metrics(
    metrics_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = MetricsService(db)
    await service.delete(metrics_id, current_user.id)
