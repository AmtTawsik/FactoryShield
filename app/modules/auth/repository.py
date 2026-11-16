from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.factories.models import FactoryMembership


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> None:
        self.session.add(user)

    async def get_factory_ids(self, user_id: int) -> set[int]:
        result = await self.session.scalars(
            select(FactoryMembership.factory_id).where(FactoryMembership.user_id == user_id)
        )
        return set(result)
