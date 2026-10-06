"""Database engine, session factory, and FastAPI session dependency.

Kept synchronous on purpose: FastAPI runs sync endpoints in a threadpool, so a
sync SQLAlchemy session is simpler here and avoids a second async driver.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from taller.shared.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model in the application."""


def build_engine(database_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine for the given (or configured) database URL."""
    url = database_url or get_settings().database_url
    return create_engine(url, pool_pre_ping=True)


engine: Engine = build_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session]:
    """FastAPI dependency that yields a request-scoped SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
