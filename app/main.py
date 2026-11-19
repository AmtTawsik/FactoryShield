import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import check_database, engine
from app.core.errors import register_exception_handlers
from app.mcp.http import MCP_PATH, create_mcp_http_app
from app.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not await check_database():
        logger.warning("Database is not reachable at startup; requests that need it will return 503")
    async with app.state.mcp_sessions.run():
        yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_exception_handlers(app)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )
    app.include_router(api_router)

    mcp_app, app.state.mcp_sessions = create_mcp_http_app()
    app.router.add_route(MCP_PATH, mcp_app, methods=["GET", "POST", "DELETE"], include_in_schema=False)
    return app


app = create_app()
