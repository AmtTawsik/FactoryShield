from app.core.time import today
from app.modules.chat.repository import FactoryContextRepository
from app.modules.factories.models import Factory

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


def build_factory_list(factories: list[Factory], total: int) -> str:
    """Factories the user may ask about in a conversation that is not tied to one factory."""
    if not factories:
        return "This user has no factories assigned, so no factory records are available."
    lines = ["Factories this user can access (use the ID in tool calls):"]
    lines += [f"- ID {factory.id}: {factory.name} ({factory.district})" for factory in factories]
    if total > len(factories):
        lines.append(f"- ... and {total - len(factories)} more")
    return "\n".join(lines)
