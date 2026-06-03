from fastapi import HTTPException, status


class APEXException(Exception):
    """Base APEX exception."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ── Auth ─────────────────────────────────────────────────────────────────────

class CredentialsException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(CredentialsException):
    def __init__(self):
        super().__init__(detail="Token has expired")


class InvalidTokenException(CredentialsException):
    def __init__(self):
        super().__init__(detail="Invalid token")


# ── Resources ────────────────────────────────────────────────────────────────

class NotFoundException(HTTPException):
    def __init__(self, resource: str, identifier: str | int = ""):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AlreadyExistsException(HTTPException):
    def __init__(self, resource: str, field: str = ""):
        detail = f"{resource} already exists"
        if field:
            detail = f"{resource} with this {field} already exists"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
