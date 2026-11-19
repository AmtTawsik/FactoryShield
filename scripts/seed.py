import asyncio
from datetime import date, datetime, time, timedelta, timezone

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    CorrectiveAction,
    Factory,
    FactoryMembership,
    Organization,
    SafetyIncident,
    SafetyInspection,
    User,
)
from app.modules.auth.models import UserRole
from app.modules.corrective_actions.models import ActionStatus
from app.modules.inspections.models import InspectionStatus

DHAKA = timezone(timedelta(hours=6))
TODAY = date.today()


class SeedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    seed_super_admin_password: str = Field(min_length=8)
    seed_admin_password: str = Field(min_length=8)
    seed_staff_password: str = Field(min_length=8)


SUPER_ADMIN = ("Abdullah Al Mubin", "amttawsik.cse@gmail.com")

MAIN_ORGANIZATION = "Meghna Apparel Group"
ADMIN = ("Farhana Rahman", "farhana.rahman@factoryshield.demo")

STAFF_MEMBERS = [
    ("Mahmudul Hasan", "mahmudul.hasan@factoryshield.demo", ["FL-GZP-04512", "FL-GZP-07731"]),
    ("Nusrat Jahan", "nusrat.jahan@factoryshield.demo", ["FL-NGJ-02218"]),
    ("Arif Hossain", "arif.hossain@factoryshield.demo", ["FL-CTG-05107", "FL-DHK-03390", "FL-DHK-06044"]),
]

# Inspections: (days ago, negative = upcoming, category, score or None if scheduled, findings)
# Incidents:   (days ago, "HH:MM", type, severity, location, injured, description, status)
# Actions:     (linked to ("inspection" | "incident", index), title, priority, assigned to,
#               due in days, negative = past, status)
FACTORIES = [
    {
        "license_number": "FL-GZP-04512",
        "name": "Sonali Thread Knit Composite Ltd",
        "address": "Plot 14, Konabari BSCIC Industrial Area, Gazipur",
        "district": "Gazipur",
        "worker_count": 1450,
        "floor_count": 6,
        "contact_person": "Kamrul Islam",
        "contact_phone": "+8801700000101",
        "inspections": [
            (-10, "fire", None, "Quarterly fire drill and extinguisher audit."),
            (25, "fire", 72, "Two extinguishers on sewing floor 3 past refill date. Exit sign on stair B not "
                            "lit. Fire drill completed in 4 min 10 sec."),
            (48, "chemical", 64, "Dyeing section: chemical containers without GHS labels, low water pressure "
                                "at the eye-wash station, MSDS missing for three dyes."),
            (80, "electrical", 81, "Main DB room clear and locked. Loose cable trays above cutting tables on "
                                  "floor 2. Thermography due next quarter."),
        ],
        "incidents": [
            (6, "10:40", "injury", "medium", "Cutting section, floor 2", 1,
             "Operator's left hand cut by a straight knife cutter; chain-mail glove not worn. First aid given "
             "and referred to clinic, 3 days leave.", "investigating"),
            (19, "15:15", "chemical", "high", "Dyeing section", 2,
             "Caustic soda splashed while pouring from a drum without a pump. Two workers had skin irritation; "
             "eyes rinsed at the eye-wash station.", "closed"),
            (33, "21:05", "near_miss", "low", "Finishing, floor 5", 0,
             "Steam iron left on during shift change; line supervisor switched it off before it scorched the "
             "table.", "closed"),
        ],
        "actions": [
            (("inspection", 1), "Refill and retag expired extinguishers on floor 3", "high",
             "Fire Safety Officer", -10, "open"),
            (("inspection", 1), "Repair exit sign lighting on stair B", "medium", "Maintenance Team", -5,
             "in_progress"),
            (("inspection", 2), "Label all chemical containers with GHS labels in Bangla and English", "high",
             "Dyeing Section In-charge", 7, "in_progress"),
            (("inspection", 2), "Restore eye-wash station water pressure", "high", "Maintenance Team", -20,
             "completed"),
            (("incident", 0), "Enforce chain-mail glove use at all straight knife cutters", "high",
             "Cutting Manager", 3, "open"),
        ],
    },
    {
        "license_number": "FL-GZP-07731",
        "name": "Bangshi Denim Works Ltd",
        "address": "Station Road, Tongi, Gazipur",
        "district": "Gazipur",
        "worker_count": 860,
        "floor_count": 5,
        "contact_person": "Shahidul Alam",
        "contact_phone": "+8801700000102",
        "inspections": [
            (-20, "ppe", None, "PPE availability and use in washing and dry process."),
            (5, "electrical", 58, "Overloaded sockets at the washing plant panel, two MCBs bypassed, no "
                                 "earthing test record since last year."),
            (40, "general", 77, "Housekeeping fair. First-aid boxes on floors 1 and 4 incomplete. Drinking "
                               "water test report available."),
            (70, "structural", 83, "Hairline plaster cracks on floor 4 column C7 under monitoring; no new "
                                  "cracks since last assessment. Floor load signs in place."),
        ],
        "incidents": [
            (2, "11:20", "electrical", "high", "Washing plant", 0,
             "Sparking at the panel feeding hydro-extractor 2. Machine isolated and electrician called.",
             "open"),
            (27, "14:00", "injury", "low", "Dry process, hand sanding", 1,
             "Dust in a worker's eye during hand sanding; goggles not worn. Eye rinsed, no further treatment.",
             "closed"),
            (55, "09:30", "near_miss", "medium", "Stair A, floor 3", 0,
             "Fabric bundles stacked on the stair landing partly blocked the exit route. Removed after report.",
             "closed"),
        ],
        "actions": [
            (("inspection", 1), "Replace bypassed MCBs and rebalance the washing plant panel", "high",
             "Electrical Engineer", -1, "in_progress"),
            (("inspection", 1), "Carry out earthing resistance test and keep the record", "medium",
             "Electrical Engineer", 10, "open"),
            (("inspection", 2), "Restock first-aid boxes on floors 1 and 4", "low", "Admin & HR", -30,
             "completed"),
            (("incident", 0), "Thermographic scan of all washing plant panels", "high", "Electrical Engineer",
             5, "open"),
            (("incident", 1), "Issue goggles and make them mandatory in dry process", "medium",
             "Dry Process Supervisor", -12, "open"),
        ],
    },
    {
        "license_number": "FL-NGJ-02218",
        "name": "Padma Stitch Apparels Ltd",
        "address": "BSCIC Industrial Estate, Fatullah, Narayanganj",
        "district": "Narayanganj",
        "worker_count": 620,
        "floor_count": 4,
        "contact_person": "Rezaul Karim",
        "contact_phone": "+8801700000103",
        "inspections": [
            (-7, "electrical", None, "Annual electrical safety inspection by external engineer."),
            (15, "fire", 85, "Fire alarm tested and audible on all floors. Hose reel on floor 2 missing its "
                            "nozzle."),
            (45, "ppe", 69, "Needle guards missing on 11 machines in sewing line 4; masks not used in the "
                           "trimming section."),
            (90, "general", 74, "Ventilation weak on floor 4. Child-care room ready but rarely used. Toilet "
                               "count adequate."),
        ],
        "incidents": [
            (9, "16:45", "injury", "medium", "Sewing line 4", 1,
             "Needle went through an operator's finger; the needle guard had been removed. First aid and "
             "tetanus injection given.", "investigating"),
            (38, "13:10", "fire", "low", "Generator room", 0,
             "Oily rag near the generator exhaust caught fire; put out with a CO2 extinguisher within a "
             "minute.", "closed"),
            (61, "10:05", "near_miss", "low", "Floor 4 corridor", 0,
             "Wet floor near the washroom without a warning sign; a worker slipped but was not hurt.",
             "closed"),
        ],
        "actions": [
            (("inspection", 2), "Refit needle guards on line 4 and check all other lines", "high",
             "Production Manager", -8, "in_progress"),
            (("inspection", 1), "Replace missing hose reel nozzle on floor 2", "medium", "Fire Safety Officer",
             -25, "completed"),
            (("inspection", 3), "Install two exhaust fans on floor 4", "medium", "Maintenance Team", 20,
             "open"),
            (("incident", 1), "Keep generator room free of oily waste and add a metal bin with lid", "low",
             "Maintenance Team", -35, "completed"),
            (("incident", 0), "Retrain line 4 operators on needle guard use", "medium", "HR & Compliance", 4,
             "open"),
        ],
    },
    {
        "license_number": "FL-CTG-05107",
        "name": "Karnaphuli Seamline Garments Ltd",
        "address": "Sector 3, Chattogram EPZ, Chattogram",
        "district": "Chattogram",
        "worker_count": 1980,
        "floor_count": 7,
        "contact_person": "Tanvir Ahmed",
        "contact_phone": "+8801700000104",
        "inspections": [
            (-14, "fire", None, "Night-shift evacuation drill."),
            (10, "structural", 79, "Column retrofitting on the ground floor complete. Roof water tank load "
                                  "needs review by a structural engineer."),
            (30, "fire", 88, "Sprinkler pump tested. Fire doors self-closing, but the floor 6 door was kept "
                            "open with a wedge."),
            (60, "chemical", 71, "Spot-cleaning chemicals kept on the sewing floor; no secondary containment "
                                "in the chemical store."),
        ],
        "incidents": [
            (4, "23:40", "fire", "medium", "Floor 6 packing store", 0,
             "Smoke from an overheated tube light fitting above the packing store. Power cut and fitting "
             "replaced.", "investigating"),
            (22, "08:15", "structural", "high", "Roof", 0,
             "Water leaking through the roof slab around the water tank after heavy rain; area cordoned off.",
             "investigating"),
            (47, "12:50", "injury", "low", "Packing section", 1,
             "Carton fell from a stack onto a worker's foot; minor bruise.", "closed"),
        ],
        "actions": [
            (("inspection", 1), "Structural engineer to review roof water tank load", "high",
             "Factory Engineer", -3, "open"),
            (("inspection", 2), "Remove door wedges and brief supervisors on fire door rules", "medium",
             "Floor Supervisors", -26, "completed"),
            (("inspection", 3), "Move spot-cleaning chemicals to the store and add drip trays", "medium",
             "Compliance Officer", -15, "in_progress"),
            (("incident", 0), "Replace old tube light fittings in floor 6 stores with LED", "medium",
             "Electrical Engineer", 12, "open"),
            (("incident", 1), "Waterproof the roof slab around the water tank", "high", "Factory Engineer",
             15, "open"),
        ],
    },
    {
        "license_number": "FL-DHK-03390",
        "name": "Turag Weave Fashions Ltd",
        "address": "Zirabo, Ashulia, Savar, Dhaka",
        "district": "Dhaka",
        "worker_count": 1120,
        "floor_count": 6,
        "contact_person": "Nasrin Akter",
        "contact_phone": "+8801700000105",
        "inspections": [
            (-28, "structural", None, "Annual building condition check."),
            (3, "general", 66, "Main exit gate partly blocked by trucks during loading. Fire blanket missing "
                              "in the canteen kitchen."),
            (35, "electrical", 75, "Generator room ventilation adequate. Taped cable joints on floor 5 lines "
                                  "need proper junction boxes."),
            (65, "fire", 80, "Fire drill completed in 3 min 40 sec. 18 trained fire fighters on the roster."),
        ],
        "incidents": [
            (12, "17:30", "injury", "high", "Loading bay", 1,
             "Worker's leg trapped between a truck and the loading platform; taken to hospital with a hairline "
             "fracture.", "investigating"),
            (29, "12:20", "near_miss", "medium", "Canteen kitchen", 0,
             "Gas cylinder hose found leaking during lunch. Cylinder closed and hose replaced.", "closed"),
            (52, "10:45", "electrical", "low", "Sewing floor 5", 0,
             "Burning smell from a taped cable joint under line 12. Power isolated and joint redone.",
             "closed"),
        ],
        "actions": [
            (("inspection", 1), "Mark and keep the main exit route clear during loading", "high",
             "Security In-charge", -2, "in_progress"),
            (("inspection", 1), "Install a fire blanket in the canteen kitchen", "low", "Admin & HR", 6,
             "open"),
            (("inspection", 2), "Replace taped cable joints on floor 5 with junction boxes", "medium",
             "Electrical Engineer", -18, "open"),
            (("incident", 0), "Add wheel stoppers and a banksman at the loading bay", "high",
             "Logistics Manager", 2, "open"),
            (("incident", 1), "Monthly check of canteen gas hoses and regulators", "medium",
             "Canteen Supervisor", -22, "completed"),
        ],
    },
    {
        "license_number": "FL-DHK-06044",
        "name": "Dhaleshwari Sweaters Ltd",
        "address": "Section 7, Mirpur, Dhaka",
        "district": "Dhaka",
        "worker_count": 340,
        "floor_count": 3,
        "contact_person": "Monirul Haque",
        "contact_phone": "+8801700000106",
        "inspections": [
            (-3, "fire", None, "Follow-up check on the second exit stair."),
            (20, "fire", 61, "Only one exit stair usable; stair 2 used for yarn storage. Extinguishers present "
                            "but staff not trained to use them."),
            (50, "ppe", 78, "Masks used in linking section. No ear protection in the knitting section."),
            (85, "electrical", 70, "Knitting machine wiring acceptable. No emergency lighting on floor 3."),
        ],
        "incidents": [
            (16, "14:35", "near_miss", "high", "Stair 2", 0,
             "During a power cut workers could not use stair 2 because of stored yarn cartons.", "closed"),
            (41, "11:00", "injury", "low", "Knitting section", 1,
             "Finger pinched while clearing a yarn jam with the machine running.", "closed"),
            (73, "19:20", "electrical", "medium", "Floor 3 ironing area", 0,
             "Power socket melted under an extension board feeding two irons.", "closed"),
        ],
        "actions": [
            (("inspection", 1), "Clear stair 2 and keep it free of storage", "high", "Factory Manager", -14,
             "completed"),
            (("inspection", 1), "Fire extinguisher training for all workers", "high", "Fire Safety Officer",
             -6, "open"),
            (("inspection", 2), "Provide ear plugs in the knitting section", "medium", "Admin & HR", 9,
             "open"),
            (("inspection", 3), "Install emergency lighting on floor 3", "medium", "Maintenance Team", -40,
             "in_progress"),
            (("incident", 2), "Remove extension boards from ironing tables and add fixed sockets", "medium",
             "Maintenance Team", -60, "completed"),
        ],
    },
]

SECOND_ORGANIZATION = "Shapla Knitwear Ltd"
SECOND_ADMIN = ("Sabrina Akter", "sabrina.akter@shapla.demo")
SECOND_STAFF_MEMBERS = [
    ("Rakib Hossain", "rakib.hossain@shapla.demo", ["FL-SVR-03871", "FL-GZP-09124"]),
]
SECOND_FACTORIES = [
    {
        "license_number": "FL-SVR-03871",
        "name": "Shapla Knitwear Ashulia Unit",
        "address": "Plot 7, Baipail, Ashulia, Savar",
        "district": "Dhaka",
        "worker_count": 820,
        "floor_count": 5,
        "contact_person": "Mizanur Rahman",
        "contact_phone": "+8801700000201",
        "inspections": [
            (-6, "electrical", None, "Annual thermography of the main distribution boards."),
            (21, "fire", 77, "Fire alarm audible on all floors. One hose reel on floor 4 blocked by cartons. "
                            "Drill evacuation time 3 min 40 sec."),
            (64, "structural", 70, "Hairline cracks in the floor 5 slab near the lift core; engineer review "
                                  "recommended. Roof water tank load within limits."),
        ],
        "incidents": [
            (9, "11:20", "electrical", "medium", "Knitting section, floor 2", 0,
             "Sparks from a loose socket feeding a knitting machine; power cut at the panel and socket "
             "replaced.", "closed"),
            (28, "18:45", "injury", "low", "Packing, floor 1", 1,
             "Worker's foot bruised by a falling carton from an overloaded rack; first aid given.", "closed"),
        ],
        "actions": [
            (("inspection", 1), "Clear the hose reel on floor 4 and mark a no-storage zone", "high",
             "Floor Manager", -3, "open"),
            (("inspection", 2), "Structural engineer to assess floor 5 slab cracks", "high",
             "Factory Engineer", 12, "in_progress"),
            (("incident", 1), "Limit rack loading in packing and fix the rack labels", "medium",
             "Packing Supervisor", -15, "completed"),
        ],
    },
    {
        "license_number": "FL-GZP-09124",
        "name": "Shapla Knitwear Tongi Unit",
        "address": "Cherag Ali Market Road, Tongi, Gazipur",
        "district": "Gazipur",
        "worker_count": 540,
        "floor_count": 4,
        "contact_person": "Nasrin Sultana",
        "contact_phone": "+8801700000202",
        "inspections": [
            (14, "ppe", 66, "Ear protection missing in the knitting hall; eight operators without masks in "
                           "the dusty linking section."),
            (45, "general", 79, "Canteen and toilets clean; first-aid boxes on floors 2 and 3 short of "
                               "bandages."),
        ],
        "incidents": [
            (5, "09:30", "near_miss", "medium", "Linking section, floor 3", 0,
             "Overloaded extension board found warm to touch before the shift; removed by the electrician.",
             "investigating"),
        ],
        "actions": [
            (("inspection", 0), "Issue ear plugs and dust masks and record daily checks", "high",
             "Compliance Officer", -2, "in_progress"),
            (("inspection", 1), "Restock first-aid boxes on floors 2 and 3", "low", "Admin & HR", 4, "open"),
            (("incident", 0), "Replace extension boards in linking with fixed sockets", "medium",
             "Maintenance Team", 10, "open"),
        ],
    },
]

ORGANIZATIONS = [
    (MAIN_ORGANIZATION, ADMIN, STAFF_MEMBERS, FACTORIES),
    (SECOND_ORGANIZATION, SECOND_ADMIN, SECOND_STAFF_MEMBERS, SECOND_FACTORIES),
]


async def get_or_create_organization(session: AsyncSession, name: str, admin_email: str) -> tuple[Organization, bool]:
    organization = await session.scalar(select(Organization).where(func.lower(Organization.name) == name.lower()))
    if organization:
        return organization, False
    admin = await session.scalar(select(User).where(User.email == admin_email))
    if admin is not None and admin.organization is not None:
        admin.organization.name = name
        return admin.organization, False
    organization = Organization(name=name)
    session.add(organization)
    await session.flush()
    return organization, True


async def get_or_create_user(
    session: AsyncSession, full_name: str, email: str, password: str, role: UserRole, organization_id: int | None
) -> tuple[User, bool]:
    user = await session.scalar(select(User).where(User.email == email))
    if user:
        return user, False
    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        organization_id=organization_id,
    )
    session.add(user)
    await session.flush()
    return user, True


def build_factory_records(factory: Factory, data: dict, staff_member: User) -> list:
    inspections = []
    for days_ago, category, score, findings in data["inspections"]:
        inspections.append(
            SafetyInspection(
                factory=factory,
                inspector=staff_member,
                inspection_date=TODAY - timedelta(days=days_ago),
                category=category,
                status=InspectionStatus.SCHEDULED if score is None else InspectionStatus.COMPLETED,
                score=score,
                findings=findings,
            )
        )

    incidents = []
    for days_ago, clock, incident_type, severity, location, injured, description, status in data["incidents"]:
        occurred_on = TODAY - timedelta(days=days_ago)
        incidents.append(
            SafetyIncident(
                factory=factory,
                reported_by=staff_member,
                occurred_at=datetime.combine(occurred_on, time.fromisoformat(clock), tzinfo=DHAKA),
                incident_type=incident_type,
                severity=severity,
                location=location,
                injured_count=injured,
                description=description,
                status=status,
            )
        )

    actions = []
    for (source, index), title, priority, assigned_to, due_in, status in data["actions"]:
        due_date = TODAY + timedelta(days=due_in)
        completed_at = None
        if status == ActionStatus.COMPLETED:
            completed_at = datetime.combine(due_date - timedelta(days=2), time(16, 0), tzinfo=DHAKA)
        actions.append(
            CorrectiveAction(
                factory=factory,
                inspection=inspections[index] if source == "inspection" else None,
                incident=incidents[index] if source == "incident" else None,
                title=title,
                priority=priority,
                assigned_to=assigned_to,
                due_date=due_date,
                status=status,
                completed_at=completed_at,
            )
        )

    return inspections + incidents + actions


async def seed() -> None:
    settings = SeedSettings()
    created = {"organizations": 0, "users": 0, "factories": 0, "memberships": 0, "records": 0}

    async with SessionLocal() as session:
        _, is_new = await get_or_create_user(
            session, *SUPER_ADMIN, settings.seed_super_admin_password, UserRole.SUPER_ADMIN, None
        )
        created["users"] += is_new

        for name, admin, staff_members, factories in ORGANIZATIONS:
            organization, is_new = await get_or_create_organization(session, name, admin[1])
            created["organizations"] += is_new

            _, is_new = await get_or_create_user(
                session, *admin, settings.seed_admin_password, UserRole.ADMIN, organization.id
            )
            created["users"] += is_new

            staff_by_license: dict[str, User] = {}
            for full_name, email, licenses in staff_members:
                staff_member, is_new = await get_or_create_user(
                    session, full_name, email, settings.seed_staff_password, UserRole.STAFF, organization.id
                )
                created["users"] += is_new
                for license_number in licenses:
                    staff_by_license[license_number] = staff_member

            for data in factories:
                factory_fields = {key: value for key, value in data.items() if not isinstance(value, list)}
                factory = await session.scalar(
                    select(Factory).where(
                        Factory.license_number == data["license_number"], Factory.organization_id == organization.id
                    )
                )
                staff_member = staff_by_license[data["license_number"]]
                if factory is None:
                    factory = Factory(**factory_fields, organization_id=organization.id)
                    session.add(factory)
                    records = build_factory_records(factory, data, staff_member)
                    session.add_all(records)
                    await session.flush()
                    created["factories"] += 1
                    created["records"] += len(records)

                if await session.get(FactoryMembership, (staff_member.id, factory.id)) is None:
                    session.add(FactoryMembership(user_id=staff_member.id, factory_id=factory.id))
                    created["memberships"] += 1

        await session.commit()

    await engine.dispose()
    print(
        "Seed complete: {organizations} organizations, {users} users, {factories} factories, "
        "{memberships} memberships, {records} inspections/incidents/actions created.".format(**created)
    )


if __name__ == "__main__":
    asyncio.run(seed())
