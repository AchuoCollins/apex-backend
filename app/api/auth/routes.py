from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshRequest,
    LogoutRequest, TokenResponse, AccessTokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive tokens",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.login(data)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    service = AuthService(db)
    return await service.refresh(data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token",
)
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.logout(data.refresh_token)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all refresh tokens for current user",
)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.logout_all(current_user.id)
