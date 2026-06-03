from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.focus_area_service import FocusAreaService
from app.schemas.focus_area import FocusAreaCreate, FocusAreaBulkSet, FocusAreaResponse

router = APIRouter(prefix="/focus-areas", tags=["Focus Areas"])


@router.get(
    "",
    response_model=list[FocusAreaResponse],
    summary="List the current user's focus areas",
)
async def list_focus_areas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FocusAreaResponse]:
    service = FocusAreaService(db)
    return await service.list_for_user(current_user.id)


@router.post(
    "",
    response_model=FocusAreaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a focus area for the current user",
)
async def add_focus_area(
    data: FocusAreaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FocusAreaResponse:
    service = FocusAreaService(db)
    return await service.add(current_user.id, data)


@router.put(
    "",
    response_model=list[FocusAreaResponse],
    summary="Replace all focus areas for the current user",
)
async def replace_focus_areas(
    data: FocusAreaBulkSet,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FocusAreaResponse]:
    service = FocusAreaService(db)
    return await service.replace_all(current_user.id, data)


@router.delete(
    "/{focus_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a focus area by id",
)
async def delete_focus_area(
    focus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = FocusAreaService(db)
    await service.delete(focus_id, current_user.id)
