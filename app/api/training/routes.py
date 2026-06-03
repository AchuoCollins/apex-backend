from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.training_service import TrainingService
from app.services.pdf_service import TrainingPlanPDFService
from app.schemas.training import (
    TrainingPlanCreate, TrainingPlanUpdate,
    TrainingPlanResponse, TrainingPlanSummary,
    TrainingPlanGenerateRequest,
)

router = APIRouter(prefix="/training", tags=["Training Plans"])


@router.get(
    "",
    response_model=list[TrainingPlanSummary],
    summary="Get all training plans for current user",
)
async def get_training_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TrainingPlanSummary]:
    service = TrainingService(db)
    return await service.get_list(current_user.id, skip=skip, limit=limit)


@router.get(
    "/{plan_id}",
    response_model=TrainingPlanResponse,
    summary="Get a specific training plan with all exercises",
)
async def get_training_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    service = TrainingService(db)
    return await service.get_by_id(plan_id, current_user.id)


@router.post(
    "",
    response_model=TrainingPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom training plan",
)
async def create_training_plan(
    data: TrainingPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    service = TrainingService(db)
    return await service.create(current_user.id, data)


@router.post(
    "/generate",
    response_model=TrainingPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Auto-generate a training plan using goal, focus areas, and event context",
)
async def generate_training_plan(
    data: TrainingPlanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    service = TrainingService(db)
    return await service.generate(current_user.id, data)


@router.put(
    "/{plan_id}",
    response_model=TrainingPlanResponse,
    summary="Update a training plan",
)
async def update_training_plan(
    plan_id: int,
    data: TrainingPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    service = TrainingService(db)
    return await service.update(plan_id, current_user.id, data)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a training plan",
)
async def delete_training_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = TrainingService(db)
    await service.delete(plan_id, current_user.id)


@router.get(
    "/{plan_id}/pdf",
    summary="Download a PDF copy of the training plan",
    response_class=StreamingResponse,
)
async def export_training_plan_pdf(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    pdf_service = TrainingPlanPDFService(db)
    buffer, filename = await pdf_service.generate(plan_id, current_user.id)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
