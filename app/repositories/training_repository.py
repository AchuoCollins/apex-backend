from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.training_plan import TrainingPlan, TrainingPlanExercise
from app.repositories.base import BaseRepository


class TrainingPlanRepository(BaseRepository[TrainingPlan]):
    model = TrainingPlan

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user(self, user_id: int, *, skip: int = 0, limit: int = 20) -> list[TrainingPlan]:
        result = await self.session.execute(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == user_id)
            .order_by(TrainingPlan.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_with_exercises(self, plan_id: int, user_id: int) -> TrainingPlan | None:
        result = await self.session.execute(
            select(TrainingPlan)
            .options(
                selectinload(TrainingPlan.exercises).selectinload(TrainingPlanExercise.exercise)
            )
            .where(TrainingPlan.id == plan_id, TrainingPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_user(self, user_id: int) -> TrainingPlan | None:
        result = await self.session.execute(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == user_id, TrainingPlan.is_active.is_(True))
            .order_by(TrainingPlan.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_plan_for_user(self, plan_id: int, user_id: int) -> TrainingPlan | None:
        result = await self.session.execute(
            select(TrainingPlan).where(
                TrainingPlan.id == plan_id,
                TrainingPlan.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
