import logging

from mcp.server.streamable_http_manager import StreamableHTTPASGIApp, StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from sqlalchemy.exc import InterfaceError, OperationalError
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.database import SessionLocal
from app.core.errors import AppError, error_response
from app.mcp.identity import BearerTokenIdentity
from app.mcp.server import DATABASE_UNAVAILABLE, create_mcp_server
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService

logger = logging.getLogger(__name__)

MCP_PATH = "/mcp"


class BearerAuthMiddleware:

    def __init__(self, app: ASGIApp):
        self.app = app
        self.identity = BearerTokenIdentity()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = {name.decode("latin-1"): value.decode("latin-1") for name, value in scope["headers"]}
            try:
                async with SessionLocal() as session:
                    await self.identity.user(AuthService(session, UserRepository(session)), headers)
            except AppError as exc:
                await error_response(exc.status_code, exc.message)(scope, receive, send)
                return
            except (OperationalError, InterfaceError, ConnectionError, TimeoutError) as exc:
                logger.error("MCP authentication failed: database unavailable (%s)", type(exc).__name__)
                await error_response(503, DATABASE_UNAVAILABLE)(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_mcp_http_app() -> tuple[ASGIApp, StreamableHTTPSessionManager]:
    server = create_mcp_server(BearerTokenIdentity())
    # stateless: every request is authenticated on its own
    server.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    sessions = server.session_manager
    return BearerAuthMiddleware(StreamableHTTPASGIApp(sessions)), sessions
