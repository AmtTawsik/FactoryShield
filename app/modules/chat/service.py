import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page
from app.core.time import now
from app.integrations.embeddings.errors import EmbeddingUnavailableError
from app.integrations.llm.client import LLMClient
from app.integrations.llm.errors import LLMUnavailableError
from app.integrations.llm.schemas import ChatMessage as LLMMessage
from app.modules.auth.models import User
from app.modules.auth.service import FactoryScope
from app.modules.chat.context import build_factory_context, build_factory_list, build_knowledge_context
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
from app.modules.chat.tools import ChatTools, ToolContext
from app.modules.factories.schemas import FactoryFilters
from app.modules.factories.service import FactoryService
from app.modules.knowledge.schemas import KnowledgeSource
from app.modules.knowledge.service import KnowledgeService

logger = logging.getLogger(__name__)

# Only the most recent turns are sent to the model; the full history stays in the database.
HISTORY_LIMIT = 20
TITLE_LENGTH = 80
# Upper bounds for one user message: model rounds that may call tools, and tool calls per round.
MAX_TOOL_ROUNDS = 4
MAX_TOOL_CALLS_PER_ROUND = 5
FACTORY_LIST_LIMIT = 50
# Document chunks given to the model per message.
KNOWLEDGE_RESULTS = 5


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        chats: ChatRepository,
        records: FactoryContextRepository,
        factories: FactoryService,
        tools: ChatTools,
        knowledge: KnowledgeService,
    ):
        self.session = session
        self.chats = chats
        self.records = records
        self.factories = factories
        self.tools = tools
        self.knowledge = knowledge

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

        context = await self._context(conversation, scope)
        knowledge, sources = await self._knowledge(data.message, conversation, scope)
        reply, tools_used = await self._answer(
            llm,
            [context, knowledge, *history, LLMMessage("user", data.message)],
            ToolContext(scope=scope, default_factory_id=conversation.factory_id),
        )

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
        return ChatResponse(
            conversation_id=conversation.id,
            factory_id=conversation.factory_id,
            reply=reply,
            tools_used=tools_used,
            sources=sources,
        )

    async def _answer(
        self, llm: LLMClient, messages: list[LLMMessage], tool_context: ToolContext
    ) -> tuple[str, list[str]]:
        """Lets the model call tools until it answers, within the round limit."""
        tools_used: list[str] = []
        for _ in range(MAX_TOOL_ROUNDS):
            response = await llm.complete(messages, self.tools.definitions)
            if not response.tool_calls:
                return _require_text(response.content), tools_used

            calls = response.tool_calls[:MAX_TOOL_CALLS_PER_ROUND]
            messages.append(LLMMessage("assistant", response.content, tool_calls=calls))
            for call in calls:
                result = await self.tools.run(call, tool_context)
                messages.append(LLMMessage("tool", result, tool_call_id=call.id))
                if call.name not in tools_used:
                    tools_used.append(call.name)

        # Round limit reached: ask for a final answer from the results collected so far, without tools.
        logger.warning("Tool round limit reached; requesting an answer without tools")
        response = await llm.complete(messages)
        return _require_text(response.content), tools_used

    async def _context(self, conversation: Conversation, scope: FactoryScope) -> LLMMessage:
        if conversation.factory_id is not None:
            # Checked on every message, so staff removed from a factory lose access to its records.
            factory = await self.factories.get(conversation.factory_id, scope)
            return LLMMessage("system", await build_factory_context(factory, self.records))
        page = await self.factories.list(FactoryFilters(size=FACTORY_LIST_LIMIT), scope)
        return LLMMessage("system", build_factory_list(page.items, page.total))

    async def _knowledge(
        self, message: str, conversation: Conversation, scope: FactoryScope
    ) -> tuple[LLMMessage, list[KnowledgeSource]]:
        """Searches the documents for the latest message; a failed search leaves the chat working without them."""
        if conversation.factory_id is not None:
            # A factory conversation sees general documents and that factory's own, not other factories'.
            scope = FactoryScope(organization_id=scope.organization_id, factory_ids=frozenset({conversation.factory_id}))
        try:
            results = await self.knowledge.search(message, scope, limit=KNOWLEDGE_RESULTS)
        except EmbeddingUnavailableError:
            logger.warning("Document search unavailable; answering without documents")
            results = None
        text, sources = build_knowledge_context(results)
        return LLMMessage("system", text), sources

    async def list(self, filters: ConversationFilters, user: User, scope: FactoryScope) -> Page[ConversationResponse]:
        # Conversations about a factory the user can no longer see are hidden, like the factory itself.
        items, total = await self.chats.list_conversations(user.id, filters, scope.factory_ids)
        return Page(
            items=[ConversationResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def get(self, conversation_id: int, user: User, scope: FactoryScope) -> ConversationDetail:
        conversation = await self._get_own(conversation_id, user)
        if conversation.factory_id is not None and not scope.allows(conversation.factory_id):
            raise NotFoundError("Conversation not found")
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


def _require_text(content: str | None) -> str:
    if not content:
        logger.error("LLM finished without a text answer")
        raise LLMUnavailableError()
    return content


def _title(message: str) -> str:
    first_line = message.splitlines()[0].strip()
    if len(first_line) <= TITLE_LENGTH:
        return first_line
    return first_line[: TITLE_LENGTH - 3].rstrip() + "..."
