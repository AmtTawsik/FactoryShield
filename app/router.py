from fastapi import APIRouter

from app.modules.auth.controller import router as auth_router
from app.modules.chat.controller import router as chat_router
from app.modules.corrective_actions.controller import router as corrective_actions_router
from app.modules.factories.controller import router as factories_router
from app.modules.incidents.controller import router as incidents_router
from app.modules.inspections.controller import router as inspections_router
from app.modules.knowledge.controller import router as knowledge_router

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth_router)
api_router.include_router(factories_router)
api_router.include_router(inspections_router)
api_router.include_router(incidents_router)
api_router.include_router(corrective_actions_router)
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
