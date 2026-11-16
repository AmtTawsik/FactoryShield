import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    register_exception_handlers,
)


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (NotFoundError("Factory not found"), 404),
        (ConflictError("Email already registered"), 409),
        (UnauthorizedError("Invalid or expired token"), 401),
        (ForbiddenError("Admin access required"), 403),
    ],
)
def test_app_errors_return_status_and_detail(error: AppError, status_code: int):
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/fail")
    async def fail():
        raise error

    response = TestClient(app).get("/fail")

    assert response.status_code == status_code
    assert response.json() == {"detail": error.message}
