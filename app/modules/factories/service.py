from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import Page
from app.modules.auth.service import FactoryScope
from app.modules.factories.models import Factory
from app.modules.factories.repository import FactoryRepository
from app.modules.factories.schemas import FactoryCreate, FactoryFilters, FactoryResponse, FactoryUpdate

DUPLICATE_LICENSE = "A factory with this licence number already exists"


class FactoryService:
    def __init__(self, session: AsyncSession, factories: FactoryRepository):
        self.session = session
        self.factories = factories

    async def list(self, filters: FactoryFilters, scope: FactoryScope) -> Page[FactoryResponse]:
        items, total = await self.factories.list(filters, scope.factory_ids)
        return Page(
            items=[FactoryResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def get(self, factory_id: int, scope: FactoryScope) -> Factory:
        factory = await self.factories.get(factory_id)
        if factory is None or not scope.allows(factory.id):
            raise NotFoundError("Factory not found")
        return factory

    async def create(self, data: FactoryCreate, scope: FactoryScope) -> Factory:
        if await self.factories.get_by_license(data.license_number, scope.organization_id):
            raise ConflictError(DUPLICATE_LICENSE)
        factory = Factory(**data.model_dump(), organization_id=scope.organization_id)
        self.factories.add(factory)
        await self._commit(factory)
        return factory

    async def update(self, factory_id: int, data: FactoryUpdate, scope: FactoryScope) -> Factory:
        factory = await self.get(factory_id, scope)
        changes = data.changes()
        new_license = changes.get("license_number")
        if (
            new_license
            and new_license != factory.license_number
            and await self.factories.get_by_license(new_license, factory.organization_id)
        ):
            raise ConflictError(DUPLICATE_LICENSE)
        for field, value in changes.items():
            setattr(factory, field, value)
        await self._commit(factory)
        return factory

    async def delete(self, factory_id: int, scope: FactoryScope) -> None:
        factory = await self.get(factory_id, scope)
        await self.factories.delete(factory)
        await self.session.commit()

    async def _commit(self, factory: Factory) -> None:
        await self.session.commit()
        await self.session.refresh(factory)
