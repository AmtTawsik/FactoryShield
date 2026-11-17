from app.core.time import today
from app.modules.chat.repository import FactoryContextRepository
from app.modules.factories.models import Factory
from app.modules.knowledge.models import ContentStatus
from app.modules.knowledge.schemas import KnowledgeSearchResult, KnowledgeSource

RECENT_INSPECTIONS = 5


async def build_factory_context(factory: Factory, records: FactoryContextRepository) -> str:
    """Plain-text summary of one factory's records, given to the assistant as evidence."""
    on_date = today()
    inspections = await records.recent_inspections(factory.id, RECENT_INSPECTIONS)
    inspection_lines = [
        f"  - {item.inspection_date}: {item.category} inspection, score {item.score}/100" for item in inspections
    ] or ["  - none recorded"]
    scheduled = await records.count_scheduled_inspections(factory.id)
    unclosed = await records.count_unclosed_incidents(factory.id)
    serious = await records.count_unclosed_incidents(factory.id, serious_only=True)
    pending = await records.count_pending_actions(factory.id)
    overdue = await records.count_overdue_actions(factory.id, on_date)

    lines = [
        f"Factory records from the FactoryShield database (as of {on_date}):",
        f"- Factory ID {factory.id}: {factory.name}, licence {factory.license_number}, "
        f"{factory.district} district; "
        f"{factory.worker_count} workers, {factory.floor_count} floors.",
        f"- Latest completed inspections (up to {RECENT_INSPECTIONS}):",
        *inspection_lines,
        f"- Scheduled inspections: {scheduled}",
        f"- Incidents not yet closed: {unclosed} (high or critical: {serious})",
        f"- Corrective actions not completed: {pending} (overdue: {overdue})",
        "Use the tools for inspection details, overdue corrective actions and recent incidents. "
        "Without tool results, these are the only records available. Inspection findings, incident details "
        "and individual corrective actions are not included.",
    ]
    return "\n".join(lines)


def build_knowledge_context(results: list[KnowledgeSearchResult] | None) -> tuple[str, list[KnowledgeSource]]:
    """Document search results for the latest message, numbered by document, and the documents behind them.

    `None` means the search could not run. The sources come from the database, so the reply can only
    point to documents that were really retrieved.
    """
    if results is None:
        return (
            "Document search is unavailable right now, so no documents were checked for the user's latest "
            "message. If the question needs document knowledge, say the documents could not be searched at "
            "the moment. Do not cite any document.",
            [],
        )
    if not results:
        return (
            "Document search found no relevant information in the available documents for the user's latest "
            "message. If the question needs document knowledge (laws, regulations or safety guidance), say "
            "clearly that you could not find relevant information in the available documents. Do not cite "
            "any document.",
            [],
        )

    by_document: dict[int, list[KnowledgeSearchResult]] = {}
    for result in results:
        by_document.setdefault(result.document_id, []).append(result)

    sources: list[KnowledgeSource] = []
    lines = ["Document search results for the user's latest message (most relevant first):"]
    for number, chunks in enumerate(by_document.values(), start=1):
        document = chunks[0]
        sources.append(
            KnowledgeSource(
                document_id=document.document_id,
                title=document.title,
                source_authority=document.source_authority,
                source_url=document.source_url,
                content_status=document.content_status,
                verified_on=document.verified_on,
            )
        )
        status = (
            f"official text, checked on {document.verified_on}"
            if document.content_status == ContentStatus.OFFICIAL_VERIFIED
            else "general guidance, not a legal requirement in Bangladesh"
        )
        lines.append(f'[{number}] "{document.title}"')
        link = f", {document.source_url}" if document.source_url else ""
        lines.append(f"    Source: {document.source_authority}{link}")
        lines.append(f"    Status: {status}")
        lines += [f"    Excerpt: {chunk.content}" for chunk in sorted(chunks, key=lambda chunk: chunk.chunk_index)]
    lines.append(
        "These are the only documents available for this message. Cite them by number and exact title, "
        'for example [1] "Title". Do not cite documents, sections or links that are not listed here.'
    )
    return "\n".join(lines), sources


def build_factory_list(factories: list[Factory], total: int) -> str:
    """Factories the user may ask about in a conversation that is not tied to one factory."""
    if not factories:
        return "This user has no factories assigned, so no factory records are available."
    lines = ["Factories this user can access (use the ID in tool calls):"]
    lines += [f"- ID {factory.id}: {factory.name} ({factory.district})" for factory in factories]
    if total > len(factories):
        lines.append(f"- ... and {total - len(factories)} more")
    return "\n".join(lines)
