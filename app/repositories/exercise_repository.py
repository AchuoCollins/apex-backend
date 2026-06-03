from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exercise import Exercise, MuscleGroup, Difficulty
from app.repositories.base import BaseRepository


class ExerciseRepository(BaseRepository[Exercise]):
    model = Exercise

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_active(self, *, skip: int = 0, limit: int = 100) -> list[Exercise]:
        result = await self.session.execute(
            select(Exercise)
            .where(Exercise.is_active.is_(True))
            .order_by(Exercise.muscle_group, Exercise.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_muscle_group(
        self, muscle_group: MuscleGroup, *, difficulty: Difficulty | None = None
    ) -> list[Exercise]:
        stmt = (
            select(Exercise)
            .where(Exercise.muscle_group == muscle_group, Exercise.is_active.is_(True))
            .order_by(Exercise.name)
        )
        if difficulty:
            stmt = stmt.where(Exercise.difficulty == difficulty)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Exercise | None:
        result = await self.session.execute(
            select(Exercise).where(Exercise.name == name)
        )
        return result.scalar_one_or_none()

    async def name_exists(self, name: str) -> bool:
        result = await self.session.execute(
            select(Exercise.id).where(Exercise.name == name)
        )
        return result.scalar_one_or_none() is not None
