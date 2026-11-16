import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import InterfaceError, OperationalError

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


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)


async def database_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Database unavailable on %s %s: %r", request.method, request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Database is temporarily unavailable"})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    for error in (OperationalError, InterfaceError, ConnectionError, TimeoutError):
        app.add_exception_handler(error, database_unavailable_handler)
