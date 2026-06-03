from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.models.exercise import Exercise, MuscleGroup, Difficulty
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseFilter


class ExerciseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ExerciseRepository(session)

    async def get_all(
        self, filters: ExerciseFilter, skip: int = 0, limit: int = 100
    ) -> list[ExerciseResponse]:
        if filters.muscle_group:
            items = await self.repo.get_by_muscle_group(
                filters.muscle_group, difficulty=filters.difficulty
            )
        else:
            items = await self.repo.get_active(skip=skip, limit=limit)

        # Apply remaining filters in-memory (small dataset)
        if filters.equipment:
            items = [e for e in items if e.equipment == filters.equipment]
        if filters.exercise_type:
            items = [e for e in items if e.exercise_type == filters.exercise_type]

        return [ExerciseResponse.model_validate(e) for e in items]

    async def get_by_id(self, exercise_id: int) -> ExerciseResponse:
        obj = await self.repo.get_by_id(exercise_id)
        if not obj:
            raise NotFoundException("Exercise", exercise_id)
        return ExerciseResponse.model_validate(obj)

    async def create(self, data: ExerciseCreate) -> ExerciseResponse:
        if await self.repo.name_exists(data.name):
            raise AlreadyExistsException("Exercise", "name")
        obj = Exercise(**data.model_dump())
        obj = await self.repo.create(obj)
        return ExerciseResponse.model_validate(obj)

    async def update(self, exercise_id: int, data: ExerciseUpdate) -> ExerciseResponse:
        obj = await self.repo.get_by_id(exercise_id)
        if not obj:
            raise NotFoundException("Exercise", exercise_id)
        update_data = data.model_dump(exclude_none=True)
        obj = await self.repo.update(obj, **update_data)
        return ExerciseResponse.model_validate(obj)

    async def delete(self, exercise_id: int) -> None:
        obj = await self.repo.get_by_id(exercise_id)
        if not obj:
            raise NotFoundException("Exercise", exercise_id)
        await self.repo.update(obj, is_active=False)  # Soft delete
