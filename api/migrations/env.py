from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importing a feature's ORM models module registers its tables on
# Base.metadata (via the declarative class bodies), which is what
# 'autogenerate' diffs against. Each feature's adapters.models module must
# be imported here, even though nothing in this file calls it directly.
import taller.identity.adapters.models  # noqa: F401,E402
import taller.inventory.adapters.models  # noqa: F401,E402
from taller.shared.config import Settings
from taller.shared.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata used for 'autogenerate' support.
target_metadata = Base.metadata


# Indexes only the migrations define, because the models cannot express them
# (the active-name unique index is functional and partial, over the
# taller_unaccent_lower() SQL function). Without this list, autogenerate reads
# them as "removed" and emits drop_index for them.
MIGRATION_ONLY_INDEXES = frozenset({"ix_inventory_items_active_name"})


def include_object(
    obj: object, name: str | None, type_: str, reflected: bool, compare_to: object
) -> bool:
    return not (
        type_ == "index" and reflected and compare_to is None and name in MIGRATION_ONLY_INDEXES
    )


def get_url() -> str:
    """Resolve the database URL from application Settings.

    Settings() (not the cached get_settings()) is used so the value always
    reflects the current environment, which matters for the test suite:
    it temporarily overrides TALLER_DATABASE_URL before running migrations
    against the test database.
    """
    return Settings().database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
