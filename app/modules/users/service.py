from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.core.pagination import Page
from app.core.security import hash_password
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.users.repository import UserAdminRepository
from app.modules.users.schemas import UserCreate, UserDetail, UserFilters, UserUpdate

DUPLICATE_EMAIL = "An account with this email already exists"


class UserService:

    def __init__(self, session: AsyncSession, users: UserRepository, admin_users: UserAdminRepository):
        self.session = session
        self.users = users
        self.admin_users = admin_users

    async def get(self, user_id: int, admin: User) -> UserDetail:
        return await self._detail(await self._get(user_id, admin))

    async def create(self, data: UserCreate, admin: User) -> UserDetail:
        if await self.users.get_by_email(data.email):
            raise ConflictError(DUPLICATE_EMAIL)
        await self._check_factories(data.factory_ids, admin)
        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            organization_id=admin.organization_id,
        )
        self.users.add(user)
        await self.session.flush()
        await self.admin_users.replace_factories(user.id, data.factory_ids)
        await self.session.commit()
        return await self.get(user.id, admin)

    async def update(self, user_id: int, data: UserUpdate, current: User) -> UserDetail:
        user = await self._get(user_id, current)
        changes = data.changes()
        if user.id == current.id and (
            changes.get("role", UserRole.ADMIN) != UserRole.ADMIN or changes.get("is_active", True) is False
        ):
            raise InvalidDataError("You cannot remove your own admin role or deactivate your own account")
        password = changes.pop("password", None)
        if password is not None:
            user.password_hash = hash_password(password)
        for field, value in changes.items():
            setattr(user, field, value)
        await self.session.commit()
        return await self.get(user.id, current)

    async def set_factories(self, user_id: int, factory_ids: list[int], admin: User) -> UserDetail:
        user = await self._get(user_id, admin)
        await self._check_factories(factory_ids, admin)
        await self.admin_users.replace_factories(user.id, factory_ids)
        await self.session.commit()
        return await self.get(user.id, admin)

    async def _get(self, user_id: int, admin: User) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None or user.organization_id != admin.organization_id:
            raise NotFoundError("User not found")
        return user

    async def _detail(self, user: User) -> UserDetail:
        await self.session.refresh(user)
        factories = await self.admin_users.factory_ids_by_user([user.id])
        return _to_detail(user, factories[user.id])

    async def _check_factories(self, factory_ids: list[int], admin: User) -> None:
        known = await self.admin_users.existing_factory_ids(factory_ids, admin.organization_id)
        missing = sorted(set(factory_ids) - known)
        if missing:
            raise InvalidDataError(f"Unknown factory IDs: {', '.join(map(str, missing))}")

    async def list(self, filters: UserFilters, admin: User) -> Page[UserDetail]:
        users, total = await self.admin_users.list(filters, admin.organization_id)
        factories = await self.admin_users.factory_ids_by_user([user.id for user in users])
        return Page(
            items=[_to_detail(user, factories[user.id]) for user in users],
            total=total,
            page=filters.page,
            size=filters.size,
        )


def _to_detail(user: User, factory_ids: list[int]) -> UserDetail:
    return UserDetail(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        factory_ids=factory_ids,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
