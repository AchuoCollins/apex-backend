from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.body_metrics import BodyMetrics
from app.repositories.base import BaseRepository


class MetricsRepository(BaseRepository[BodyMetrics]):
    model = BodyMetrics

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user(
        self, user_id: int, *, skip: int = 0, limit: int = 50
    ) -> list[BodyMetrics]:
        result = await self.session.execute(
            select(BodyMetrics)
            .where(BodyMetrics.user_id == user_id)
            .order_by(desc(BodyMetrics.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, metrics_id: int, user_id: int) -> BodyMetrics | None:
        result = await self.session.execute(
            select(BodyMetrics).where(
                BodyMetrics.id == metrics_id,
                BodyMetrics.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_by_user(self, user_id: int) -> BodyMetrics | None:
        result = await self.session.execute(
            select(BodyMetrics)
            .where(BodyMetrics.user_id == user_id)
            .order_by(desc(BodyMetrics.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: int) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(BodyMetrics).where(BodyMetrics.user_id == user_id)
        )
        return result.scalar_one()
