from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.exceptions import (
    CredentialsException, AlreadyExistsException, BadRequestException,
)
from app.core.config import settings
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import RefreshTokenRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, AccessTokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        if await self.user_repo.email_exists(data.email):
            raise AlreadyExistsException("User", "email")

        user = User(
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            email=data.email.lower().strip(),
            password_hash=hash_password(data.password),
        )
        user = await self.user_repo.create(user)

        # Create empty profile
        profile = UserProfile(user_id=user.id)
        self.session.add(profile)
        await self.session.flush()

        return await self._issue_tokens(user.id)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_active_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise CredentialsException("Invalid email or password")

        return await self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        token_obj = await self.token_repo.get_valid_token(refresh_token)
        if not token_obj:
            raise CredentialsException("Invalid or expired refresh token")

        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise CredentialsException("Invalid token type")

        # Rotate — revoke old, issue new
        await self.token_repo.revoke_token(refresh_token)

        user_id = int(payload["sub"])
        access_token = create_access_token(user_id)
        return AccessTokenResponse(access_token=access_token)

    async def logout(self, refresh_token: str) -> None:
        await self.token_repo.revoke_token(refresh_token)

    async def logout_all(self, user_id: int) -> None:
        await self.token_repo.revoke_all_for_user(user_id)

    # ── Private ───────────────────────────────────────────────────────────────

    async def _issue_tokens(self, user_id: int) -> TokenResponse:
        access_token  = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        token_obj = RefreshToken(
            user_id=user_id,
            token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.session.add(token_obj)
        await self.session.flush()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
