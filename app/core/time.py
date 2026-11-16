from datetime import UTC, date, datetime, timedelta, timezone

DHAKA_TZ = timezone(timedelta(hours=6), name="Asia/Dhaka")


def today() -> date:
    """Business date in Bangladesh, independent of the server's timezone."""
    return datetime.now(DHAKA_TZ).date()


def now() -> datetime:
    return datetime.now(UTC)
