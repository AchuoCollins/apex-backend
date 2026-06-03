from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_focus_area import UserFocusArea
from app.repositories.base import BaseRepository


class FocusAreaRepository(BaseRepository[UserFocusArea]):
    model = UserFocusArea

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user(self, user_id: int) -> list[UserFocusArea]:
        result = await self.session.execute(
            select(UserFocusArea)
            .where(UserFocusArea.user_id == user_id)
            .order_by(UserFocusArea.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, focus_id: int, user_id: int) -> UserFocusArea | None:
        result = await self.session.execute(
            select(UserFocusArea).where(
                UserFocusArea.id == focus_id,
                UserFocusArea.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: int, focus_area: str) -> UserFocusArea | None:
        result = await self.session.execute(
            select(UserFocusArea).where(
                UserFocusArea.user_id == user_id,
                UserFocusArea.focus_area == focus_area,
            )
        )
        return result.scalar_one_or_none()

    async def delete_all_for_user(self, user_id: int) -> None:
        await self.session.execute(
            delete(UserFocusArea).where(UserFocusArea.user_id == user_id)
        )
        await self.session.flush()
