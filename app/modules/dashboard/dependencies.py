from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.service import DashboardService
from app.modules.factories.dependencies import get_factory_service


def get_dashboard_service(session: DbSession) -> DashboardService:
    return DashboardService(DashboardRepository(session), get_factory_service(session))


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
