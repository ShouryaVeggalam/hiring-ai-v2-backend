"""Application-wide exception hierarchy and FastAPI exception handlers."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger

logger = get_logger(__name__)


class CelestraError(Exception):
    """Base class for all domain errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "celestra_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(CelestraError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"


class ConflictError(CelestraError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"


class ValidationFailedError(CelestraError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_failed"


class AuthenticationError(CelestraError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "authentication_failed"


class AuthorizationError(CelestraError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "authorization_failed"


class AgentExecutionError(CelestraError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "agent_execution_failed"


def _error_body(error_code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": error_code, "message": message, "details": details or {}}}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers to the FastAPI app."""

    @app.exception_handler(CelestraError)
    async def _celestra_handler(_: Request, exc: CelestraError) -> JSONResponse:
        logger.warning("domain_error", code=exc.error_code, message=exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("validation_error", "Request validation failed", {"errors": exc.errors()}),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_handler(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("integrity_error", error=str(exc.orig))
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body("integrity_error", "Database constraint violated"),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_error", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("internal_error", "An unexpected error occurred"),
        )
