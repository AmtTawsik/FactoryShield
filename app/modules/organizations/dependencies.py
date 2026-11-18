from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.auth.dependencies import AuthServiceDep
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.service import OrganizationService


def get_organization_service(session: DbSession, auth: AuthServiceDep) -> OrganizationService:
    return OrganizationService(session, OrganizationRepository(session), auth)


OrganizationServiceDep = Annotated[OrganizationService, Depends(get_organization_service)]
