# Centralized error handling for API endpoints.
# Converts custom exceptions to HTTP responses.
from fastapi import HTTPException, status

from app.core.exceptions import (AppException, AuthenticationError,
                                 AuthorizationError, DatabaseError,
                                 NotFoundError, ServiceError)
from app.core.exceptions import TimeoutError as AppTimeoutError
from app.core.exceptions import ValidationError


def handle_app_exception(e: AppException) -> HTTPException:
    # Convert AppException to HTTPException with appropriate status code.
    if isinstance(e, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    elif isinstance(e, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    elif isinstance(e, AuthenticationError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    elif isinstance(e, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    elif isinstance(e, DatabaseError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    elif isinstance(e, ServiceError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.message
        )
    elif isinstance(e, AppTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=e.message
        )
    else:
        return HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
