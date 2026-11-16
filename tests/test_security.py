from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password_hash = hash_password("Gazipur#2024")

    assert password_hash != "Gazipur#2024"
    assert verify_password("Gazipur#2024", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_round_trip():
    token = create_access_token(42)

    assert decode_access_token(token) == 42


def test_expired_token_is_rejected():
    past = datetime.now(UTC) - timedelta(hours=2)
    token = jwt.encode(
        {"sub": "42", "iat": past, "exp": past + timedelta(minutes=5)},
        get_settings().jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(UnauthorizedError):
        decode_access_token(token)


def test_token_signed_with_other_key_is_rejected():
    token = jwt.encode({"sub": "42"}, "another-secret-key-that-is-long-enough", algorithm=JWT_ALGORITHM)

    with pytest.raises(UnauthorizedError):
        decode_access_token(token)
