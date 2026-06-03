from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.body_metrics import BodyMetrics
from app.repositories.metrics_repository import MetricsRepository
from app.schemas.metrics import MetricsCreate, MetricsUpdate, MetricsResponse, MetricsList


class MetricsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MetricsRepository(session)

    async def create(self, user_id: int, data: MetricsCreate) -> MetricsResponse:
        obj = BodyMetrics(user_id=user_id, **data.model_dump())
        obj = await self.repo.create(obj)
        return MetricsResponse.model_validate(obj)

    async def get_list(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> MetricsList:
        items = await self.repo.get_by_user(user_id, skip=skip, limit=limit)
        total = await self.repo.count_by_user(user_id)
        return MetricsList(
            items=[MetricsResponse.model_validate(m) for m in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_by_id(self, metrics_id: int, user_id: int) -> MetricsResponse:
        obj = await self.repo.get_by_id_and_user(metrics_id, user_id)
        if not obj:
            raise NotFoundException("Metrics", metrics_id)
        return MetricsResponse.model_validate(obj)

    async def update(
        self, metrics_id: int, user_id: int, data: MetricsUpdate
    ) -> MetricsResponse:
        obj = await self.repo.get_by_id_and_user(metrics_id, user_id)
        if not obj:
            raise NotFoundException("Metrics", metrics_id)

        update_data = data.model_dump(exclude_none=True)
        obj = await self.repo.update(obj, **update_data)
        return MetricsResponse.model_validate(obj)

    async def delete(self, metrics_id: int, user_id: int) -> None:
        obj = await self.repo.get_by_id_and_user(metrics_id, user_id)
        if not obj:
            raise NotFoundException("Metrics", metrics_id)
        await self.repo.delete(obj)

    async def get_latest(self, user_id: int) -> MetricsResponse | None:
        obj = await self.repo.get_latest_by_user(user_id)
        return MetricsResponse.model_validate(obj) if obj else None
