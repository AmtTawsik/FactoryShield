from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import Page
from app.core.security import hash_password
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import DUPLICATE_EMAIL, DUPLICATE_ORGANIZATION, AuthService
from app.modules.organizations.models import Organization
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import (
    AdminAccountCreate,
    OrganizationAdmin,
    OrganizationCreate,
    OrganizationDetail,
    OrganizationFilters,
    OrganizationItem,
    OrganizationUpdate,
)


class OrganizationService:

    def __init__(self, session: AsyncSession, organizations: OrganizationRepository, auth: AuthService):
        self.session = session
        self.organizations = organizations
        self.auth = auth
        self.users = UserRepository(session)

    async def get(self, organization_id: int) -> OrganizationDetail:
        organization = await self._get(organization_id)
        counts = await self.organizations.counts([organization.id])
        admins = await self.organizations.admins(organization.id)
        return OrganizationDetail(
            **_item(organization, counts[organization.id]).model_dump(),
            admins=[OrganizationAdmin.model_validate(admin) for admin in admins],
        )

    async def create(self, data: OrganizationCreate) -> OrganizationDetail:
        user = await self.auth.create_organization(
            data.name, data.admin.full_name, data.admin.email, hash_password(data.admin.password)
        )
        await self.session.commit()
        return await self.get(user.organization_id)

    async def update(self, organization_id: int, data: OrganizationUpdate) -> OrganizationDetail:
        organization = await self._get(organization_id)
        changes = data.changes()
        new_name = changes.get("name")
        if new_name and new_name.lower() != organization.name.lower():
            if await self.organizations.get_by_name(new_name):
                raise ConflictError(DUPLICATE_ORGANIZATION)
        for field, value in changes.items():
            setattr(organization, field, value)
        await self.session.commit()
        return await self.get(organization.id)

    async def add_admin(self, organization_id: int, data: AdminAccountCreate) -> OrganizationDetail:
        organization = await self._get(organization_id)
        if await self.users.get_by_email(data.email):
            raise ConflictError(DUPLICATE_EMAIL)
        self.users.add(
            User(
                full_name=data.full_name,
                email=data.email,
                password_hash=hash_password(data.password),
                role=UserRole.ADMIN,
                organization_id=organization.id,
            )
        )
        await self.session.commit()
        return await self.get(organization.id)

    async def _get(self, organization_id: int) -> Organization:
        organization = await self.organizations.get(organization_id)
        if organization is None:
            raise NotFoundError("Organization not found")
        await self.session.refresh(organization)
        return organization

    async def list(self, filters: OrganizationFilters) -> Page[OrganizationItem]:
        organizations, total = await self.organizations.list(filters)
        counts = await self.organizations.counts([organization.id for organization in organizations])
        return Page(
            items=[_item(organization, counts[organization.id]) for organization in organizations],
            total=total,
            page=filters.page,
            size=filters.size,
        )


def _item(organization: Organization, counts: tuple[int, int]) -> OrganizationItem:
    users, factories = counts
    return OrganizationItem(
        id=organization.id,
        name=organization.name,
        is_active=organization.is_active,
        user_count=users,
        factory_count=factories,
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )
