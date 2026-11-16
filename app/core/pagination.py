from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int


async def paginate(session: AsyncSession, query: Select, params: PageParams) -> tuple[list[Any], int]:
    total = await session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    items = await session.scalars(query.offset(params.offset).limit(params.size))
    return list(items), total
