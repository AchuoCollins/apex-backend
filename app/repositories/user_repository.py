from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_profile(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.focus_areas),
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email == email.lower().strip(),
                User.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none() is not None
