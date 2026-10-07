"""Per-phone login throttling: a lockout after repeated failed logins.

The state is keyed by the normalized phone number, whether or not any user
owns that phone: throttling only registered phones would let anyone learn
which numbers have accounts just by watching which ones get locked out.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from taller.identity.domain.phone_number import PhoneNumber

#: Consecutive failed logins that lock a phone.
MAX_FAILED_LOGINS = 5

#: How long a locked phone refuses every login attempt.
LOCKOUT_DURATION = timedelta(minutes=15)


@dataclass(slots=True)
class LoginThrottle:
    """Failed-login bookkeeping for one phone number."""

    phone: PhoneNumber
    failed_attempts: int
    locked_until: datetime | None

    def remaining_lock(self, now: datetime) -> timedelta | None:
        """Time left on an active lock, or None when the phone may log in."""
        if self.locked_until is None or self.locked_until <= now:
            return None
        return self.locked_until - now

    def record_failure(self, now: datetime) -> None:
        """Count a failed login, locking the phone when it hits the limit.

        A lock that has already expired starts the count from zero, so one
        typo right after a lockout does not lock the phone again.
        """
        if self.locked_until is not None and self.locked_until <= now:
            self.failed_attempts = 0
            self.locked_until = None
        self.failed_attempts += 1
        if self.failed_attempts >= MAX_FAILED_LOGINS:
            self.locked_until = now + LOCKOUT_DURATION

    def record_success(self) -> None:
        """A successful login clears every earlier failure."""
        self.failed_attempts = 0
        self.locked_until = None
