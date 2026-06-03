from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.core.exceptions import CredentialsException, NotFoundException
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise CredentialsException("Invalid or expired token")

    if payload.get("type") != "access":
        raise CredentialsException("Wrong token type")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise CredentialsException("Token missing subject")

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id_str))

    if not user or not user.is_active:
        raise CredentialsException("User not found or inactive")

    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Superuser access required")
    return current_user
