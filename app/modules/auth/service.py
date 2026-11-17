from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse

INVALID_LOGIN_MESSAGE = "Invalid email or password"

# Verifying against this hash when the email is unknown keeps login timing the same
# for unknown emails and wrong passwords.
_UNKNOWN_USER_HASH = hash_password("unknown-user-placeholder")


@dataclass(frozen=True)
class FactoryScope:
    """Factories the current user may access. `None` means every factory (admin)."""

    factory_ids: frozenset[int] | None

    def allows(self, factory_id: int) -> bool:
        return self.factory_ids is None or factory_id in self.factory_ids

    def ensure_factory(self, factory_id: int) -> None:
        # 404 instead of 403 so users cannot discover which factory IDs exist.
        if not self.allows(factory_id):
            raise NotFoundError("Factory not found")


class AuthService:
    def __init__(self, session: AsyncSession, users: UserRepository):
        self.session = session
        self.users = users

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_by_email(data.email):
            raise ConflictError("An account with this email already exists")

        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserRole.STAFF,
        )
        self.users.add(user)
        await self.session.commit()
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(data.email)
        if user is None:
            verify_password(data.password, _UNKNOWN_USER_HASH)
            raise UnauthorizedError(INVALID_LOGIN_MESSAGE)
        if not verify_password(data.password, user.password_hash) or not user.is_active:
            raise UnauthorizedError(INVALID_LOGIN_MESSAGE)

        expire_minutes = get_settings().jwt_expire_minutes
        return TokenResponse(access_token=create_access_token(user.id), expires_in=expire_minutes * 60)

    async def get_active_user(self, user_id: int) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired token")
        return user

    async def get_factory_scope(self, user: User) -> FactoryScope:
        if user.role == UserRole.ADMIN:
            return FactoryScope(factory_ids=None)
        return FactoryScope(factory_ids=frozenset(await self.users.get_factory_ids(user.id)))
