"""Domain errors for the identity feature (workshops, users, sessions)."""

from datetime import timedelta


class InvalidPhoneNumber(ValueError):
    """Raised when a value cannot be normalized into a valid Honduran phone number."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid Honduran phone number: {raw!r}")
        self.raw = raw


class PhoneAlreadyRegistered(Exception):
    """Raised when registering a user whose phone number is already taken."""

    def __init__(self, phone: str) -> None:
        super().__init__(f"Phone number already registered: {phone}")
        self.phone = phone


class InvalidCredentials(Exception):
    """Raised when a login attempt's phone/password combination is wrong.

    Also raised when the phone is not registered at all: both cases must be
    indistinguishable to the caller, so there is a single error for both.
    """


class TooManyLoginAttempts(Exception):
    """Raised when a phone is locked out after repeated failed logins.

    Raised before the password is checked, for registered and unregistered
    phones alike.
    """

    def __init__(self, retry_after: timedelta) -> None:
        super().__init__(f"Login locked; retry after {retry_after}")
        self.retry_after = retry_after


class NotAuthenticated(Exception):
    """Raised when a session token is missing, malformed, tampered, or expired."""
