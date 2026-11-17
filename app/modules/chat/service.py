from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page
from app.core.time import now
from app.integrations.llm.client import LLMClient
from app.integrations.llm.schemas import ChatMessage as LLMMessage
from app.modules.auth.models import User
from app.modules.auth.service import FactoryScope
from app.modules.chat.context import build_factory_context
from app.modules.chat.models import ChatMessage, Conversation, MessageRole
from app.modules.chat.repository import ChatRepository, FactoryContextRepository
from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationFilters,
    ConversationResponse,
    MessageResponse,
)
from app.modules.factories.service import FactoryService

# Only the most recent turns are sent to the model; the full history stays in the database.
HISTORY_LIMIT = 20
TITLE_LENGTH = 80


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        chats: ChatRepository,
        records: FactoryContextRepository,
        factories: FactoryService,
    ):
        self.session = session
        self.chats = chats
        self.records = records
        self.factories = factories

    async def send(self, data: ChatRequest, user: User, scope: FactoryScope, llm: LLMClient) -> ChatResponse:
        if data.conversation_id is not None:
            conversation = await self._get_own(data.conversation_id, user)
            stored = await self.chats.get_messages(conversation.id, HISTORY_LIMIT)
            history = [LLMMessage(message.role, message.content) for message in stored]
            new_messages = []
        else:
            conversation = Conversation(user_id=user.id, factory_id=data.factory_id, title=_title(data.message))
            history = [LLMMessage(item.role, item.content) for item in data.previous_messages]
            new_messages = [ChatMessage(role=item.role, content=item.content) for item in data.previous_messages]

        context = []
        if conversation.factory_id is not None:
            # Checked on every message, so staff removed from a factory lose access to its records.
            factory = await self.factories.get(conversation.factory_id, scope)
            context = [LLMMessage("system", await build_factory_context(factory, self.records))]

        reply = await llm.reply([*context, *history, LLMMessage("user", data.message)])

        # Saved only after the provider answered, so a failed call leaves no half-finished turn.
        new_messages += [
            ChatMessage(role=MessageRole.USER, content=data.message),
            ChatMessage(role=MessageRole.ASSISTANT, content=reply),
        ]
        conversation.updated_at = now()
        self.chats.add(conversation)
        await self.session.flush()
        for message in new_messages:
            message.conversation_id = conversation.id
        self.chats.add(*new_messages)
        await self.session.commit()
        return ChatResponse(conversation_id=conversation.id, factory_id=conversation.factory_id, reply=reply)

    async def list(self, filters: ConversationFilters, user: User) -> Page[ConversationResponse]:
        items, total = await self.chats.list_conversations(user.id, filters)
        return Page(
            items=[ConversationResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def get(self, conversation_id: int, user: User) -> ConversationDetail:
        conversation = await self._get_own(conversation_id, user)
        messages = await self.chats.get_messages(conversation.id)
        return ConversationDetail(
            **ConversationResponse.model_validate(conversation).model_dump(),
            messages=[MessageResponse.model_validate(message) for message in messages],
        )

    async def _get_own(self, conversation_id: int, user: User) -> Conversation:
        # Conversations are private to their owner, admins included.
        conversation = await self.chats.get_conversation(conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise NotFoundError("Conversation not found")
        return conversation


def _title(message: str) -> str:
    first_line = message.splitlines()[0].strip()
    if len(first_line) <= TITLE_LENGTH:
        return first_line
    return first_line[: TITLE_LENGTH - 3].rstrip() + "..."
