"""The real wall clock, behind the ``Clock`` port so tests can move time."""

from datetime import UTC, datetime


class SystemClock:
    """Reads the current UTC time from the system."""

    def now(self) -> datetime:
        return datetime.now(UTC)
