import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ResourceError, ResourceNotFoundError, ToolError
from mcp.server.mcpserver.prompts.base import UserMessage
from mcp.shared.exceptions import MCPError
from mcp_types.jsonrpc import INTERNAL_ERROR, INVALID_PARAMS
from pydantic import Field
from pydantic_core import to_jsonable_python
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.errors import AppError, NotFoundError
from app.core.schemas import MAX_ID
from app.mcp.identity import Identity
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService, FactoryScope
from app.modules.chat.context import build_factory_context
from app.modules.chat.dependencies import get_chat_tools
from app.modules.chat.repository import FactoryContextRepository
from app.modules.chat.tools import ChatTools, InspectionSummaryArgs, OverdueActionsArgs, ToolContext
from app.modules.corrective_actions.models import ActionPriority
from app.modules.factories.models import Factory

logger = logging.getLogger(__name__)

DATABASE_UNAVAILABLE = "The database is temporarily unavailable, please try again shortly"
INSTRUCTIONS = (
    "FactoryShield holds safety inspections, incidents and corrective actions for garment factories in "
    "Bangladesh. Every result is limited to the factories the signed-in user may access. Use "
    "get_factory_inspection_summary and get_overdue_corrective_actions for current records, read "
    "factory://{factory_id}/overview for a factory profile, and use the safety_inspection_review prompt to "
    "prepare a review. Report only what the results contain."
)

FactoryIdArg = Annotated[int, Field(ge=1, le=MAX_ID, description="Factory ID, as listed in FactoryShield")]


@dataclass(frozen=True)
class Access:

    session: AsyncSession
    scope: FactoryScope
    tools: ChatTools

    async def factory(self, factory_id: int) -> Factory:
        return await self.tools.factories.get(factory_id, self.scope)


ErrorFactory = Callable[[AppError | None, str], Exception]


def create_mcp_server(identity: Identity) -> MCPServer:
    server = MCPServer("FactoryShield", instructions=INSTRUCTIONS)

    @asynccontextmanager
    async def access(ctx: Context, error: ErrorFactory) -> AsyncIterator[Access]:
        try:
            async with SessionLocal() as session:
                auth = AuthService(session, UserRepository(session))
                user = await identity.user(auth, ctx.headers)
                yield Access(session, await auth.get_factory_scope(user), get_chat_tools(session))
        except AppError as exc:
            raise error(exc, exc.message) from exc
        except (OperationalError, InterfaceError, ConnectionError, TimeoutError) as exc:
            logger.error("MCP request failed: database unavailable (%s)", type(exc).__name__)
            raise error(None, DATABASE_UNAVAILABLE) from exc

    @server.tool(
        name="get_factory_inspection_summary",
        description=(
            "Inspection statistics for one factory: counts by status and category, average and lowest scores, "
            "the latest completed inspections with findings, and scheduled inspections."
        ),
    )
    async def get_factory_inspection_summary(factory_id: FactoryIdArg, ctx: Context) -> dict[str, Any]:
        async with access(ctx, _tool_error) as current:
            result = await current.tools.inspection_summary(
                InspectionSummaryArgs(factory_id=factory_id), ToolContext(current.scope, default_factory_id=None)
            )
        return to_jsonable_python(result)

    @server.tool(
        name="get_overdue_corrective_actions",
        description=(
            "Corrective actions that are not completed and past their due date, most overdue first, with days "
            "overdue, priority, status and assignee. Without factory_id it covers every factory the user can access."
        ),
    )
    async def get_overdue_corrective_actions(
        ctx: Context,
        factory_id: Annotated[int | None, Field(ge=1, le=MAX_ID, description="Limit to one factory")] = None,
        priority: Annotated[ActionPriority | None, Field(description="Only this priority")] = None,
        limit: Annotated[int, Field(ge=1, le=50, description="Maximum actions returned")] = 20,
    ) -> dict[str, Any]:
        async with access(ctx, _tool_error) as current:
            result = await current.tools.overdue_actions(
                OverdueActionsArgs(factory_id=factory_id, priority=priority, limit=limit),
                ToolContext(current.scope, default_factory_id=None),
            )
        return to_jsonable_python(result)

    @server.resource(
        "factory://{factory_id}/overview",
        name="factory_overview",
        title="Factory overview",
        description=(
            "Profile of one factory with its latest completed inspections and open counts of scheduled "
            "inspections, unclosed incidents and pending or overdue corrective actions."
        ),
        mime_type="text/plain",
    )
    async def factory_overview(factory_id: str, ctx: Context) -> str:
        factory_number = _factory_id(factory_id, ResourceNotFoundError)
        async with access(ctx, _resource_error) as current:
            factory = await current.factory(factory_number)
            return await build_factory_context(factory, FactoryContextRepository(current.session))

    @server.prompt(
        name="safety_inspection_review",
        title="Safety inspection review",
        description="Prepares a review of one factory's inspection results, open risks and overdue corrective actions.",
    )
    async def safety_inspection_review(factory_id: str, ctx: Context) -> list[UserMessage]:
        factory_number = _factory_id(factory_id, lambda message: MCPError(INVALID_PARAMS, message))
        async with access(ctx, _prompt_error) as current:
            factory = await current.factory(factory_number)
            overview = await build_factory_context(factory, FactoryContextRepository(current.session))
        return [UserMessage(_review_request(factory, overview))]

    return server


def _factory_id(value: str, error: Callable[[str], Exception]) -> int:
    if not value.isdigit() or not 1 <= int(value) <= MAX_ID:
        raise error(f"factory_id must be a whole number from 1 to {MAX_ID}")
    return int(value)


def _tool_error(exc: AppError | None, message: str) -> Exception:
    return ToolError(message)


def _resource_error(exc: AppError | None, message: str) -> Exception:
    return ResourceNotFoundError(message) if isinstance(exc, NotFoundError) else ResourceError(message)


def _prompt_error(exc: AppError | None, message: str) -> Exception:
    return MCPError(INVALID_PARAMS if isinstance(exc, NotFoundError) else INTERNAL_ERROR, message)


def _review_request(factory: Factory, overview: str) -> str:
    return f"""Prepare a safety inspection review for {factory.name} (factory ID {factory.id}).

Current records from FactoryShield:
{overview}

Steps:
1. Call get_factory_inspection_summary with factory_id {factory.id} for scores by category and recent findings.
2. Call get_overdue_corrective_actions with factory_id {factory.id} for actions past their due date.
3. Write the review with these sections:
   - Overall picture: latest scores and how they changed.
   - Weakest areas: lowest-scoring categories and repeated findings.
   - Overdue corrective actions: the most urgent first, with days overdue and who is responsible.
   - Next steps: what to fix before the next scheduled inspection.

Use only facts from these records and tool results, and label them "From the records". Mark any general
safety advice as "General guidance". Do not invent figures, laws or deadlines. This review is not an official
inspection result or a compliance certification."""
