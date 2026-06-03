from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.user_profile import UserProfile
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def get_me(self, user_id: int) -> UserResponse:
        user = await self.repo.get_by_id_with_profile(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        return UserResponse.model_validate(user)

    async def update_me(self, user_id: int, data: UserUpdate) -> UserResponse:
        user = await self.repo.get_by_id_with_profile(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        if data.first_name is not None:
            user.first_name = data.first_name.strip()
        if data.last_name is not None:
            user.last_name = data.last_name.strip()

        if data.profile is not None:
            profile = user.profile
            if profile is None:
                profile = UserProfile(user_id=user_id)
                self.session.add(profile)

            profile_data = data.profile.model_dump(exclude_none=True)
            for key, value in profile_data.items():
                setattr(profile, key, value)

        await self.session.flush()
        await self.session.refresh(user)
        return UserResponse.model_validate(user)
