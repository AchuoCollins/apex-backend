from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.event_service import EventService
from app.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "",
    response_model=list[EventResponse],
    summary="List events for the current user (chronological)",
)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    service = EventService(db)
    return await service.list_for_user(current_user.id, skip=skip, limit=limit)


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    service = EventService(db)
    return await service.create(current_user.id, data)


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get an event by id",
)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    service = EventService(db)
    return await service.get_by_id(event_id, current_user.id)


@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update an event",
)
async def update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    service = EventService(db)
    return await service.update(event_id, current_user.id, data)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = EventService(db)
    await service.delete(event_id, current_user.id)
