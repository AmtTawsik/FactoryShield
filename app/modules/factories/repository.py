from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.factories.models import Factory
from app.modules.factories.schemas import FactoryFilters


class FactoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, factory_id: int) -> Factory | None:
        return await self.session.get(Factory, factory_id)

    async def get_by_license(self, license_number: str, organization_id: int) -> Factory | None:
        return await self.session.scalar(
            select(Factory).where(Factory.license_number == license_number, Factory.organization_id == organization_id)
        )

    async def list(self, filters: FactoryFilters, factory_ids: frozenset[int] | None) -> tuple[list[Factory], int]:
        query = select(Factory)
        if factory_ids is not None:
            query = query.where(Factory.id.in_(factory_ids))
        if filters.search:
            query = query.where(
                or_(
                    Factory.name.icontains(filters.search, autoescape=True),
                    Factory.license_number.icontains(filters.search, autoescape=True),
                )
            )
        if filters.district:
            query = query.where(func.lower(Factory.district) == filters.district.lower())
        if filters.is_active is not None:
            query = query.where(Factory.is_active == filters.is_active)

        return await paginate(self.session, query.order_by(Factory.name, Factory.id), filters)

    def add(self, factory: Factory) -> None:
        self.session.add(factory)

    async def delete(self, factory: Factory) -> None:
        await self.session.delete(factory)
