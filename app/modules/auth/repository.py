from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.factories.models import Factory, FactoryMembership


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> None:
        self.session.add(user)

    async def get_factory_ids(self, user_id: int, organization_id: int) -> set[int]:
        """Factories the user is assigned to, within their own organization."""
        result = await self.session.scalars(
            select(FactoryMembership.factory_id)
            .join(Factory, Factory.id == FactoryMembership.factory_id)
            .where(FactoryMembership.user_id == user_id, Factory.organization_id == organization_id)
        )
        return set(result)

    async def get_organization_factory_ids(self, organization_id: int) -> set[int]:
        return set(await self.session.scalars(select(Factory.id).where(Factory.organization_id == organization_id)))
