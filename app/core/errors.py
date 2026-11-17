import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, InterfaceError, OperationalError, SQLAlchemyError

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    message = "Bad request"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    message = "Resource already exists"


class UnauthorizedError(AppError):
    status_code = 401
    message = "Not authenticated"


class ForbiddenError(AppError):
    status_code = 403
    message = "You do not have permission to perform this action"


class InvalidDataError(AppError):
    """Input is well-formed but breaks a business rule, e.g. an action linked to another factory's incident."""

    status_code = 422
    message = "Invalid data"


def error_response(status_code: int, detail: str, **extra) -> JSONResponse:
    """Every error body has a `detail` message; validation errors add an `errors` list."""
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return JSONResponse(status_code=status_code, content={"detail": detail, **extra}, headers=headers)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.message)


def _field_name(location: tuple) -> str:
    # ("body", "email") -> "email"; ("query", "page") -> "page"; ("body",) -> "body"
    parts = [str(part) for part in location[1:]] or [str(part) for part in location]
    return ".".join(parts)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Submitted values are not echoed back, so passwords never appear in an error response.
    errors = [
        {"field": _field_name(error["loc"]), "message": error["msg"].removeprefix("Value error, ")}
        for error in exc.errors()
    ]
    return error_response(422, "Invalid request data", errors=errors)


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    # Services check duplicates first with a clear message; this covers races and any other constraint.
    logger.warning("Integrity error on %s %s: %s", request.method, request.url.path, exc.orig)
    return error_response(409, "The request conflicts with existing data")


async def database_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Database unavailable on %s %s: %r", request.method, request.url.path, exc)
    return error_response(503, "Database is temporarily unavailable")


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response(500, "Internal server error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    for error in (OperationalError, InterfaceError, ConnectionError, TimeoutError):
        app.add_exception_handler(error, database_unavailable_handler)
    app.add_exception_handler(SQLAlchemyError, unexpected_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
