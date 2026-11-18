from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.auth.models import User
from app.modules.factories.models import Factory, FactoryMembership
from app.modules.users.schemas import UserFilters


class UserAdminRepository:
    """User listing and factory assignments for user management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def factory_ids_by_user(self, user_ids: list[int]) -> dict[int, list[int]]:
        rows = await self.session.execute(
            select(FactoryMembership.user_id, FactoryMembership.factory_id)
            .where(FactoryMembership.user_id.in_(user_ids))
            .order_by(FactoryMembership.factory_id)
        )
        result: dict[int, list[int]] = {user_id: [] for user_id in user_ids}
        for user_id, factory_id in rows:
            result[user_id].append(factory_id)
        return result

    async def existing_factory_ids(self, factory_ids: list[int], organization_id: int) -> set[int]:
        return set(
            await self.session.scalars(
                select(Factory.id).where(Factory.id.in_(factory_ids), Factory.organization_id == organization_id)
            )
        )

    async def replace_factories(self, user_id: int, factory_ids: list[int]) -> None:
        await self.session.execute(delete(FactoryMembership).where(FactoryMembership.user_id == user_id))
        self.session.add_all(FactoryMembership(user_id=user_id, factory_id=factory_id) for factory_id in factory_ids)

    # Last in the class: a method named `list` would shadow the builtin in later annotations.
    async def list(self, filters: UserFilters, organization_id: int) -> tuple[list[User], int]:
        query = select(User).where(User.organization_id == organization_id)
        if filters.search:
            query = query.where(
                or_(
                    User.full_name.icontains(filters.search, autoescape=True),
                    User.email.icontains(filters.search, autoescape=True),
                )
            )
        if filters.role:
            query = query.where(User.role == filters.role)
        if filters.is_active is not None:
            query = query.where(User.is_active == filters.is_active)
        return await paginate(self.session, query.order_by(User.full_name, User.id), filters)
