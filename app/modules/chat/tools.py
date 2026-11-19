import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta

from pydantic import BaseModel, Field, ValidationError

from app.core.errors import NotFoundError
from app.core.schemas import Id
from app.core.time import today
from app.integrations.llm.schemas import ToolCall, ToolDefinition
from app.modules.auth.service import FactoryScope
from app.modules.corrective_actions.models import ActionPriority
from app.modules.corrective_actions.schemas import ActionFilters
from app.modules.corrective_actions.service import ActionService
from app.modules.factories.service import FactoryService
from app.modules.incidents.models import IncidentSeverity, IncidentStatus
from app.modules.incidents.schemas import IncidentFilters
from app.modules.incidents.service import IncidentService
from app.modules.inspections.models import InspectionStatus
from app.modules.inspections.schemas import InspectionFilters
from app.modules.inspections.service import InspectionService

logger = logging.getLogger(__name__)

TEXT_PREVIEW = 300


class InspectionSummaryArgs(BaseModel):
    factory_id: Id | None = None


class OverdueActionsArgs(BaseModel):
    factory_id: Id | None = None
    priority: ActionPriority | None = None
    limit: int = Field(default=20, ge=1, le=50)


class IncidentSearchArgs(BaseModel):
    factory_id: Id | None = None
    days: int = Field(default=30, ge=1, le=365)
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    keyword: str | None = Field(default=None, min_length=2, max_length=100)
    limit: int = Field(default=10, ge=1, le=50)


FACTORY_ID = {"type": "integer", "description": "Factory ID. Leave out to use the conversation's factory."}

TOOL_DEFINITIONS = (
    ToolDefinition(
        name="get_factory_inspection_summary",
        description=(
            "Inspection statistics for one factory: counts by status (scheduled, completed) and category, "
            "average and lowest scores, the latest completed inspections with findings, and scheduled inspections."
        ),
        parameters={"type": "object", "properties": {"factory_id": FACTORY_ID}},
    ),
    ToolDefinition(
        name="get_overdue_corrective_actions",
        description=(
            "Corrective actions that are not completed and past their due date, with due date, days overdue, "
            "priority, status and assignee. Without a factory_id in a general conversation it covers every "
            "factory the user can access."
        ),
        parameters={
            "type": "object",
            "properties": {
                "factory_id": FACTORY_ID,
                "priority": {"type": "string", "enum": [item.value for item in ActionPriority]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Default 20"},
            },
        },
    ),
    ToolDefinition(
        name="search_recent_safety_incidents",
        description=(
            "Safety incidents from the last N days, newest first, with type, severity, status, location, "
            "injured count and description. Optional filters: severity, status, keyword in description or location."
        ),
        parameters={
            "type": "object",
            "properties": {
                "factory_id": FACTORY_ID,
                "days": {"type": "integer", "minimum": 1, "maximum": 365, "description": "Default 30"},
                "severity": {"type": "string", "enum": [item.value for item in IncidentSeverity]},
                "status": {"type": "string", "enum": [item.value for item in IncidentStatus]},
                "keyword": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Default 10"},
            },
        },
    ),
)


@dataclass(frozen=True)
class ToolContext:
    scope: FactoryScope
    default_factory_id: int | None


@dataclass(frozen=True)
class _Tool:
    arguments: type[BaseModel]
    handler: Callable[[BaseModel, ToolContext], Awaitable[dict]]


class ChatTools:

    definitions = TOOL_DEFINITIONS

    def __init__(
        self,
        factories: FactoryService,
        inspections: InspectionService,
        actions: ActionService,
        incidents: IncidentService,
    ):
        self.factories = factories
        self.inspections = inspections
        self.actions = actions
        self.incidents = incidents
        self._tools = {
            "get_factory_inspection_summary": _Tool(InspectionSummaryArgs, self.inspection_summary),
            "get_overdue_corrective_actions": _Tool(OverdueActionsArgs, self.overdue_actions),
            "search_recent_safety_incidents": _Tool(IncidentSearchArgs, self._recent_incidents),
        }

    async def run(self, call: ToolCall, context: ToolContext) -> str:
        return json.dumps(await self._run(call, context), default=str, ensure_ascii=False)

    async def _run(self, call: ToolCall, context: ToolContext) -> dict:
        tool = self._tools.get(call.name)
        if tool is None:
            return {"error": f"Unknown tool: {call.name}"}
        try:
            raw_arguments = json.loads(call.arguments or "{}")
        except json.JSONDecodeError:
            return {"error": "Tool arguments must be a JSON object"}
        if not isinstance(raw_arguments, dict):
            return {"error": "Tool arguments must be a JSON object"}
        try:
            arguments = tool.arguments.model_validate(raw_arguments)
        except ValidationError as exc:
            problems = [f"{'.'.join(map(str, error['loc'])) or 'arguments'}: {error['msg']}" for error in exc.errors()]
            return {"error": "Invalid tool arguments", "problems": problems}
        try:
            return await tool.handler(arguments, context)
        except NotFoundError as exc:
            return {"error": exc.message}

    async def inspection_summary(self, args: InspectionSummaryArgs, context: ToolContext) -> dict:
        factory_id = args.factory_id or context.default_factory_id
        if factory_id is None:
            return {"error": "factory_id is required in a conversation without a factory"}
        factory = await self.factories.get(factory_id, context.scope)
        stats = await self.inspections.statistics(factory.id, context.scope)
        completed = await self.inspections.list(
            InspectionFilters(factory_id=factory.id, status=InspectionStatus.COMPLETED, size=5), context.scope
        )
        scheduled = await self.inspections.list(
            InspectionFilters(factory_id=factory.id, status=InspectionStatus.SCHEDULED, size=5), context.scope
        )
        return {
            "factory": {"id": factory.id, "name": factory.name},
            "totals": {status.value: sum(row.count for row in stats if row.status == status) for status in InspectionStatus},
            "by_category": [row.model_dump() for row in stats],
            "latest_completed": [
                {
                    "date": item.inspection_date,
                    "category": item.category,
                    "score": item.score,
                    "findings": _preview(item.findings),
                }
                for item in completed.items
            ],
            "scheduled": [{"date": item.inspection_date, "category": item.category} for item in scheduled.items],
        }

    async def overdue_actions(self, args: OverdueActionsArgs, context: ToolContext) -> dict:
        factory_id = args.factory_id or context.default_factory_id
        if factory_id is not None:
            await self.factories.get(factory_id, context.scope)
        on_date = today()
        page = await self.actions.list(
            ActionFilters(factory_id=factory_id, priority=args.priority, overdue=True, size=args.limit),
            context.scope,
        )
        names = await self._factory_names({item.factory_id for item in page.items}, context.scope)
        return {
            "as_of": on_date,
            "total_overdue": page.total,
            "returned": len(page.items),
            "actions": [
                {
                    "id": item.id,
                    "factory": names[item.factory_id],
                    "title": item.title,
                    "priority": item.priority,
                    "status": item.status,
                    "due_date": item.due_date,
                    "days_overdue": (on_date - item.due_date).days,
                    "assigned_to": item.assigned_to,
                }
                for item in page.items
            ],
        }

    async def _recent_incidents(self, args: IncidentSearchArgs, context: ToolContext) -> dict:
        factory_id = args.factory_id or context.default_factory_id
        if factory_id is not None:
            await self.factories.get(factory_id, context.scope)
        date_from = today() - timedelta(days=args.days)
        page = await self.incidents.list(
            IncidentFilters(
                factory_id=factory_id,
                severity=args.severity,
                status=args.status,
                search=args.keyword,
                date_from=date_from,
                size=args.limit,
            ),
            context.scope,
        )
        names = await self._factory_names({item.factory_id for item in page.items}, context.scope)
        return {
            "period": {"from": date_from, "to": today()},
            "total": page.total,
            "returned": len(page.items),
            "incidents": [
                {
                    "id": item.id,
                    "factory": names[item.factory_id],
                    "occurred_at": item.occurred_at,
                    "type": item.incident_type,
                    "severity": item.severity,
                    "status": item.status,
                    "location": item.location,
                    "injured_count": item.injured_count,
                    "description": _preview(item.description),
                }
                for item in page.items
            ],
        }

    async def _factory_names(self, factory_ids: set[int], scope: FactoryScope) -> dict[int, str]:
        return {factory_id: (await self.factories.get(factory_id, scope)).name for factory_id in factory_ids}


def _preview(text: str | None) -> str | None:
    if text is None or len(text) <= TEXT_PREVIEW:
        return text
    return text[: TEXT_PREVIEW - 3].rstrip() + "..."
