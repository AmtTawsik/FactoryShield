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
        f"- Factory: {factory.name}, licence {factory.license_number}, {factory.district} district; "
        f"{factory.worker_count} workers, {factory.floor_count} floors.",
        f"- Latest completed inspections (up to {RECENT_INSPECTIONS}):",
        *inspection_lines,
        f"- Scheduled inspections: {scheduled}",
        f"- Incidents not yet closed: {unclosed} (high or critical: {serious})",
        f"- Corrective actions not completed: {pending} (overdue: {overdue})",
        "These are the only records available in this conversation. Inspection findings, incident details "
        "and individual corrective actions are not included.",
    ]
    return "\n".join(lines)
