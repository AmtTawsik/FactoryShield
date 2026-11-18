from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError, ForbiddenError, InvalidDataError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse
from app.modules.organizations.models import Organization
from app.modules.organizations.repository import OrganizationRepository

INVALID_LOGIN_MESSAGE = "Invalid email or password"
DUPLICATE_EMAIL = "An account with this email already exists"
DUPLICATE_ORGANIZATION = "An organization with this name already exists"
PLATFORM_NO_DATA_ACCESS = "The platform administrator cannot access organization records"

# Verifying against this hash when the email is unknown keeps login timing the same
# for unknown emails and wrong passwords.
_UNKNOWN_USER_HASH = hash_password("unknown-user-placeholder")


@dataclass(frozen=True)
class FactoryScope:
    """What the current user may access: their organization and the factories in it they can see.

    Admins get every factory of their organization; staff get their assigned factories. Every query
    filters on `factory_ids`, so records of other organizations are never reachable. `organization_id`
    is None only for the platform administrator, who sees the shared document library and nothing else.
    """

    organization_id: int | None
    factory_ids: frozenset[int]

    def allows(self, factory_id: int) -> bool:
        return factory_id in self.factory_ids

    def ensure_factory(self, factory_id: int) -> None:
        # 404 instead of 403 so users cannot discover which factory IDs exist.
        if not self.allows(factory_id):
            raise NotFoundError("Factory not found")


class AuthService:
    def __init__(self, session: AsyncSession, users: UserRepository):
        self.session = session
        self.users = users
        self.organizations = OrganizationRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        """Company sign-up: a new organization with the person signing up as its admin."""
        user = await self.create_organization(
            data.organization_name, data.full_name, data.email, hash_password(data.password)
        )
        await self.session.commit()
        await self.session.refresh(user, ["organization"])
        return user

    async def create_organization(self, name: str, full_name: str, email: str, password_hash: str) -> User:
        """Adds an organization and its first admin (not committed). Used by sign-up and the platform admin."""
        if await self.organizations.get_by_name(name):
            raise ConflictError(DUPLICATE_ORGANIZATION)
        if await self.users.get_by_email(email):
            raise ConflictError(DUPLICATE_EMAIL)
        organization = Organization(name=name)
        self.organizations.add(organization)
        await self.session.flush()
        user = User(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN,
            organization_id=organization.id,
        )
        self.users.add(user)
        await self.session.flush()
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(data.email)
        if user is None:
            verify_password(data.password, _UNKNOWN_USER_HASH)
            raise UnauthorizedError(INVALID_LOGIN_MESSAGE)
        if not verify_password(data.password, user.password_hash) or not _can_sign_in(user):
            raise UnauthorizedError(INVALID_LOGIN_MESSAGE)

        expire_minutes = get_settings().jwt_expire_minutes
        return TokenResponse(access_token=create_access_token(user.id), expires_in=expire_minutes * 60)

    async def change_password(self, user: User, data: ChangePasswordRequest) -> None:
        # Tokens issued before the change stay valid until they expire.
        if not verify_password(data.current_password, user.password_hash):
            raise InvalidDataError("Current password is incorrect")
        user.password_hash = hash_password(data.new_password)
        await self.session.commit()

    async def get_active_user(self, user_id: int) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None or not _can_sign_in(user):
            raise UnauthorizedError("Invalid or expired token")
        return user

    async def get_factory_scope(self, user: User) -> FactoryScope:
        """Scope for organization records. The platform administrator has none (403)."""
        if user.organization_id is None:
            raise ForbiddenError(PLATFORM_NO_DATA_ACCESS)
        if user.role == UserRole.ADMIN:
            factory_ids = await self.users.get_organization_factory_ids(user.organization_id)
        else:
            factory_ids = await self.users.get_factory_ids(user.id, user.organization_id)
        return FactoryScope(organization_id=user.organization_id, factory_ids=frozenset(factory_ids))

    async def get_knowledge_scope(self, user: User) -> FactoryScope:
        """Like the factory scope, but the platform administrator may work on the shared library."""
        if user.organization_id is None:
            return PLATFORM_SCOPE
        return await self.get_factory_scope(user)


# The shared document library only: no organization, no factories.
PLATFORM_SCOPE = FactoryScope(organization_id=None, factory_ids=frozenset())


def _can_sign_in(user: User) -> bool:
    return user.is_active and (user.organization is None or user.organization.is_active)
