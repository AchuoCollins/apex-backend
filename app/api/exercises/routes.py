from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_current_superuser
from app.models.user import User
from app.models.exercise import MuscleGroup, Difficulty, Equipment, ExerciseType
from app.services.exercise_service import ExerciseService
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseFilter

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.get(
    "",
    response_model=list[ExerciseResponse],
    summary="List exercises with optional filters",
)
async def get_exercises(
    muscle_group: MuscleGroup | None = Query(None),
    difficulty: Difficulty | None = Query(None),
    equipment: Equipment | None = Query(None),
    exercise_type: ExerciseType | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExerciseResponse]:
    service = ExerciseService(db)
    filters = ExerciseFilter(
        muscle_group=muscle_group,
        difficulty=difficulty,
        equipment=equipment,
        exercise_type=exercise_type,
    )
    return await service.get_all(filters, skip=skip, limit=limit)


@router.get(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Get an exercise by ID",
)
async def get_exercise(
    exercise_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.get_by_id(exercise_id)


@router.post(
    "",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exercise (superuser only)",
)
async def create_exercise(
    data: ExerciseCreate,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.create(data)


@router.put(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update an exercise (superuser only)",
)
async def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    service = ExerciseService(db)
    return await service.update(exercise_id, data)


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an exercise (superuser only)",
)
async def delete_exercise(
    exercise_id: int,
    _: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ExerciseService(db)
    await service.delete(exercise_id)
