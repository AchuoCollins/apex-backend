from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventUpdate, EventResponse


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = EventRepository(session)

    async def list_for_user(
        self, user_id: int, *, skip: int = 0, limit: int = 50
    ) -> list[EventResponse]:
        items = await self.repo.get_by_user(user_id, skip=skip, limit=limit)
        return [EventResponse.model_validate(i) for i in items]

    async def get_by_id(self, event_id: int, user_id: int) -> EventResponse:
        obj = await self.repo.get_by_id_and_user(event_id, user_id)
        if not obj:
            raise NotFoundException("Event", event_id)
        return EventResponse.model_validate(obj)

    async def create(self, user_id: int, data: EventCreate) -> EventResponse:
        obj = Event(
            user_id=user_id,
            event_name=data.event_name,
            event_type=data.event_type,
            event_date=data.event_date,
        )
        obj = await self.repo.create(obj)
        return EventResponse.model_validate(obj)

    async def update(
        self, event_id: int, user_id: int, data: EventUpdate
    ) -> EventResponse:
        obj = await self.repo.get_by_id_and_user(event_id, user_id)
        if not obj:
            raise NotFoundException("Event", event_id)
        update_data = data.model_dump(exclude_none=True)
        obj = await self.repo.update(obj, **update_data)
        return EventResponse.model_validate(obj)

    async def delete(self, event_id: int, user_id: int) -> None:
        obj = await self.repo.get_by_id_and_user(event_id, user_id)
        if not obj:
            raise NotFoundException("Event", event_id)
        await self.repo.delete(obj)
