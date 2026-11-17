"""MCP over stdio for MCP clients on the same machine.

Usage: uv run python -m app.mcp.stdio

The server acts as the user in MCP_STDIO_USER_EMAIL: that user's role and factory scope limit every
result. stdout carries the protocol, so all messages go to stderr.
"""

import logging
import sys

import anyio
from sqlalchemy.exc import InterfaceError, OperationalError

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.errors import AppError
from app.mcp.identity import LocalUserIdentity
from app.mcp.server import create_mcp_server
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService


async def serve() -> int:
    email = get_settings().mcp_stdio_user_email
    if email is None:
        print("error: set MCP_STDIO_USER_EMAIL in .env to the user the stdio server acts as", file=sys.stderr)
        return 1
    identity = LocalUserIdentity(email)
    try:
        async with SessionLocal() as session:
            user = await identity.user(AuthService(session, UserRepository(session)), None)
    except AppError as exc:
        print(f"error: {exc.message} ({email})", file=sys.stderr)
        return 1
    except (OperationalError, InterfaceError, ConnectionError, TimeoutError):
        print("error: the database is not reachable; check DATABASE_URL and that it is running", file=sys.stderr)
        return 1

    print(f"FactoryShield MCP (stdio) running as {user.email} ({user.role.value})", file=sys.stderr)
    try:
        await create_mcp_server(identity).run_stdio_async()
    finally:
        await engine.dispose()
    return 0


def main() -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    return anyio.run(serve)


if __name__ == "__main__":
    sys.exit(main())
