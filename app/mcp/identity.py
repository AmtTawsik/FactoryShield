from collections.abc import Mapping
from typing import Protocol

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.service import AuthService


class Identity(Protocol):
    async def user(self, auth: AuthService, headers: Mapping[str, str] | None) -> User: ...


class BearerTokenIdentity:

    async def user(self, auth: AuthService, headers: Mapping[str, str] | None) -> User:
        token = bearer_token(headers)
        if token is None:
            raise UnauthorizedError("Not authenticated")
        return await auth.get_active_user(decode_access_token(token))


class LocalUserIdentity:

    def __init__(self, email: str):
        self.email = email

    async def user(self, auth: AuthService, headers: Mapping[str, str] | None) -> User:
        user = await auth.users.get_by_email(self.email)
        if user is None:
            raise UnauthorizedError("The MCP stdio user does not exist or is inactive")
        try:
            return await auth.get_active_user(user.id)
        except UnauthorizedError:
            raise UnauthorizedError("The MCP stdio user does not exist or is inactive") from None


def bearer_token(headers: Mapping[str, str] | None) -> str | None:
    if not headers:
        return None
    value = next((value for name, value in headers.items() if name.lower() == "authorization"), "")
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
