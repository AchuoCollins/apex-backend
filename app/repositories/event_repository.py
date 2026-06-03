from datetime import datetime, timezone
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user(
        self, user_id: int, *, skip: int = 0, limit: int = 50
    ) -> list[Event]:
        result = await self.session.execute(
            select(Event)
            .where(Event.user_id == user_id)
            .order_by(asc(Event.event_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, event_id: int, user_id: int) -> Event | None:
        result = await self.session.execute(
            select(Event).where(
                Event.id == event_id,
                Event.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_next_upcoming(self, user_id: int) -> Event | None:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Event)
            .where(Event.user_id == user_id, Event.event_date >= now)
            .order_by(asc(Event.event_date))
            .limit(1)
        )
        return result.scalar_one_or_none()
