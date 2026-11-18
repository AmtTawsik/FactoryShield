from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.auth.models import User, UserRole
from app.modules.factories.models import Factory
from app.modules.organizations.models import Organization
from app.modules.organizations.schemas import OrganizationFilters


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, organization: Organization) -> None:
        self.session.add(organization)

    async def get(self, organization_id: int) -> Organization | None:
        return await self.session.get(Organization, organization_id)

    async def get_by_name(self, name: str) -> Organization | None:
        return await self.session.scalar(select(Organization).where(func.lower(Organization.name) == name.lower()))

    async def counts(self, organization_ids: list[int]) -> dict[int, tuple[int, int]]:
        """(users, factories) per organization."""
        users = dict(
            (await self.session.execute(
                select(User.organization_id, func.count())
                .where(User.organization_id.in_(organization_ids))
                .group_by(User.organization_id)
            )).all()
        )
        factories = dict(
            (await self.session.execute(
                select(Factory.organization_id, func.count())
                .where(Factory.organization_id.in_(organization_ids))
                .group_by(Factory.organization_id)
            )).all()
        )
        return {org_id: (users.get(org_id, 0), factories.get(org_id, 0)) for org_id in organization_ids}

    async def admins(self, organization_id: int) -> list[User]:
        return list(
            await self.session.scalars(
                select(User)
                .where(User.organization_id == organization_id, User.role == UserRole.ADMIN)
                .order_by(User.full_name, User.id)
            )
        )

    # Last in the class: a method named `list` would shadow the builtin in later annotations.
    async def list(self, filters: OrganizationFilters) -> tuple[list[Organization], int]:
        query = select(Organization)
        if filters.search:
            query = query.where(Organization.name.icontains(filters.search, autoescape=True))
        if filters.is_active is not None:
            query = query.where(Organization.is_active == filters.is_active)
        return await paginate(self.session, query.order_by(Organization.name, Organization.id), filters)
