import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from reshal_api.auth.models import User  # noqa: F401
from reshal_api.config import DatabaseSettings
from reshal_api.database import Base
from reshal_api.facility.models import Facility, FacilityImage  # noqa: F401
from reshal_api.payment.models import Payment  # noqa: F401
from reshal_api.reservation.models import Reservation  # noqa: F401
from reshal_api.timeframe.models import TimeFrame  # noqa: F401

db_conf = DatabaseSettings()
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
log = logging.getLogger(__name__)
config.set_main_option("sqlalchemy.url", db_conf.url)
target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    log.info("Cant run migrations in offline mode")
else:
    run_migrations_online()
