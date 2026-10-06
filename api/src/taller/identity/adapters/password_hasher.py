"""Argon2 password hashing, via pwdlib (the current FastAPI-recommended library)."""

from pwdlib import PasswordHash


class PwdlibPasswordHasher:
    """Password hasher backed by pwdlib's recommended Argon2 configuration."""

    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._password_hash.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._password_hash.verify(password, password_hash)
