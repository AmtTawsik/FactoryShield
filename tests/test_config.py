import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_missing_jwt_secret_fails(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(ValidationError, match="jwt_secret_key"):
        Settings(_env_file=None)


def test_short_jwt_secret_fails(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")

    with pytest.raises(ValidationError, match="jwt_secret_key"):
        Settings(_env_file=None)
