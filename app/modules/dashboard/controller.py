from typing import Annotated

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import CurrentFactoryScope
from app.modules.dashboard.dependencies import DashboardServiceDep
from app.modules.dashboard.schemas import DashboardFilters, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    filters: Annotated[DashboardFilters, Query()], scope: CurrentFactoryScope, service: DashboardServiceDep
):
    return await service.summary(filters, scope)
