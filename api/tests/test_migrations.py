"""The ORM models and the migrations must describe the same schema.

Defect this catches: a model change committed without its migration, or a
future `alembic revision --autogenerate` that would drop indexes the models
did not declare (the accent-insensitive active-name unique index behind
`409 item_name_taken`, and the movement history index).
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

API_ROOT = Path(__file__).resolve().parent.parent


def test_models_and_migrations_have_no_pending_operations(
    test_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TALLER_DATABASE_URL", test_engine.url.render_as_string(hide_password=False))

    command.check(Config(str(API_ROOT / "alembic.ini")))
