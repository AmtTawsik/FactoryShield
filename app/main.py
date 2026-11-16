from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.router import api_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
