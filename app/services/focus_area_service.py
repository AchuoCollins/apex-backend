from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.models.user_focus_area import UserFocusArea
from app.repositories.focus_area_repository import FocusAreaRepository
from app.schemas.focus_area import FocusAreaCreate, FocusAreaBulkSet, FocusAreaResponse


class FocusAreaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FocusAreaRepository(session)

    async def list_for_user(self, user_id: int) -> list[FocusAreaResponse]:
        items = await self.repo.get_by_user(user_id)
        return [FocusAreaResponse.model_validate(i) for i in items]

    async def add(self, user_id: int, data: FocusAreaCreate) -> FocusAreaResponse:
        existing = await self.repo.get_by_name(user_id, data.focus_area)
        if existing:
            raise AlreadyExistsException("Focus area", "focus_area")
        obj = UserFocusArea(user_id=user_id, focus_area=data.focus_area)
        obj = await self.repo.create(obj)
        return FocusAreaResponse.model_validate(obj)

    async def delete(self, focus_id: int, user_id: int) -> None:
        obj = await self.repo.get_by_id_and_user(focus_id, user_id)
        if not obj:
            raise NotFoundException("Focus area", focus_id)
        await self.repo.delete(obj)

    async def replace_all(
        self, user_id: int, data: FocusAreaBulkSet
    ) -> list[FocusAreaResponse]:
        await self.repo.delete_all_for_user(user_id)
        for name in data.focus_areas:
            self.session.add(UserFocusArea(user_id=user_id, focus_area=name))
        await self.session.flush()
        return await self.list_for_user(user_id)
