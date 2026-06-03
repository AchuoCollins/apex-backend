from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_valid_token(self, token: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_token(self, token: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(is_revoked=True)
        )
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self.session.flush()

    async def delete_expired(self) -> int:
        """Clean up expired tokens — run via scheduled task."""
        from sqlalchemy import delete, func
        result = await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.flush()
        return result.rowcount
