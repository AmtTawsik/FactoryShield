from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.chat.models import ChatMessage, Conversation
from app.modules.chat.schemas import ConversationFilters
from app.modules.corrective_actions.models import ActionStatus, CorrectiveAction
from app.modules.corrective_actions.repository import overdue_condition
from app.modules.incidents.models import IncidentSeverity, IncidentStatus, SafetyIncident
from app.modules.inspections.models import InspectionStatus, SafetyInspection


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_conversation(self, conversation_id: int) -> Conversation | None:
        return await self.session.get(Conversation, conversation_id)

    async def list_conversations(
        self, user_id: int, filters: ConversationFilters
    ) -> tuple[list[Conversation], int]:
        query = select(Conversation).where(Conversation.user_id == user_id)
        if filters.factory_id is not None:
            query = query.where(Conversation.factory_id == filters.factory_id)
        query = query.order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        return await paginate(self.session, query, filters)

    async def get_messages(self, conversation_id: int, limit: int | None = None) -> list[ChatMessage]:
        """Messages oldest first; with `limit`, only the most recent ones."""
        query = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        if limit is None:
            return list(await self.session.scalars(query.order_by(ChatMessage.id)))
        recent = await self.session.scalars(query.order_by(ChatMessage.id.desc()).limit(limit))
        return list(reversed(list(recent)))

    def add(self, *objects: Conversation | ChatMessage) -> None:
        self.session.add_all(objects)


class FactoryContextRepository:
    """Read-only summaries of one factory's records for the assistant's context."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def recent_inspections(self, factory_id: int, limit: int) -> list[SafetyInspection]:
        query = (
            select(SafetyInspection)
            .where(
                SafetyInspection.factory_id == factory_id,
                SafetyInspection.status == InspectionStatus.COMPLETED,
            )
            .order_by(SafetyInspection.inspection_date.desc(), SafetyInspection.id.desc())
            .limit(limit)
        )
        return list(await self.session.scalars(query))

    async def count_scheduled_inspections(self, factory_id: int) -> int:
        return await self._count(
            SafetyInspection,
            SafetyInspection.factory_id == factory_id,
            SafetyInspection.status == InspectionStatus.SCHEDULED,
        )

    async def count_unclosed_incidents(self, factory_id: int, serious_only: bool = False) -> int:
        conditions = [SafetyIncident.factory_id == factory_id, SafetyIncident.status != IncidentStatus.CLOSED]
        if serious_only:
            conditions.append(SafetyIncident.severity.in_([IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]))
        return await self._count(SafetyIncident, *conditions)

    async def count_pending_actions(self, factory_id: int) -> int:
        return await self._count(
            CorrectiveAction,
            CorrectiveAction.factory_id == factory_id,
            CorrectiveAction.status != ActionStatus.COMPLETED,
        )

    async def count_overdue_actions(self, factory_id: int, on_date: date) -> int:
        return await self._count(
            CorrectiveAction, CorrectiveAction.factory_id == factory_id, overdue_condition(on_date)
        )

    async def _count(self, model, *conditions) -> int:
        return await self.session.scalar(select(func.count()).select_from(model).where(*conditions))
