from typing import Any, NamedTuple

import pkg_resources
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from httpx import AsyncClient
from pytest import Config as PytestConfig
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.sql import text
from sqlalchemy.sql.elements import TextClause
from sqlalchemy_utils.functions.database import _set_url_database, make_url

from reshal_api.auth.models import User


class AuthClientFixture(NamedTuple):
    client: AsyncClient
    user: User


async def authenticate_client(client: AsyncClient, email: str, password: str):
    data = {"email": email, "password": password}

    response = await client.post("/auth/token", json=data)
    assert response.status_code == 200


# alembic_config = AlembicConfig(
#     pkg_resources.resource_filename("reshal_api", "alembic.ini")
# )
# alembic_config.set_main_option("script_location", "reshal_api:migrations")


# def _alembic_upgrade(connection: AsyncConnection):
#     alembic_config.attributes["connection"] = connection
#     alembic_command.upgrade(alembic_config, "head")


# async def run_migrations(db_url: str, echo=False):
#     engine = create_async_engine(db_url, echo=echo)
#     async with engine.begin() as conn:
#         await conn.run_sync(_alembic_upgrade)


"""
Async `sqlalchemy_utils.functions.database` functions
Only for postgres
https://github.com/kvesteri/sqlalchemy-utils/blob/master/sqlalchemy_utils/functions/database.py
"""


async def _get_scalar_result(engine: AsyncEngine, query: TextClause):
    async with engine.connect() as conn:
        return await conn.scalar(query)


async def async_database_exists(db_url: str, echo=False) -> bool:
    url = make_url(db_url)
    database = url.database
    url = _set_url_database(url, "postgres")
    engine = create_async_engine(url, echo=echo)
    try:
        return bool(
            await _get_scalar_result(
                engine, text(f"SELECT 1 FROM pg_database WHERE datname='{database}'")
            )
        )
    except (ProgrammingError, OperationalError):
        return False
    finally:
        await engine.dispose()


async def async_create_database(db_url: str, encoding="utf8", template=None):
    url = make_url(db_url)
    database = url.database
    url = _set_url_database(url, "postgres")
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")

    if not template:
        template = "template1"

    async with engine.begin() as conn:
        sql = text(
            "CREATE DATABASE {} ENCODING '{}' TEMPLATE {}".format(
                database, encoding, template
            )
        )
        await conn.execute(sql)

    await engine.dispose()


async def async_drop_database(db_url: str):
    url = make_url(db_url)
    database = url.database

    url = _set_url_database(url, "postgres")
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")

    async with engine.begin() as conn:
        version = conn.dialect.server_version_info
        pid_column = "pid" if (version >= (9, 2)) else "procpid"
        sql = text(
            """
        SELECT pg_terminate_backend(pg_stat_activity.{pid_column})
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{database}'
        AND {pid_column} <> pg_backend_pid();
        """.format(
                pid_column=pid_column, database=database
            )
        )
        await conn.execute(sql)

        sql = text(f"DROP DATABASE {database}")
        await conn.execute(sql)

    await engine.dispose()


async def get_prepared_async_engine(url: str, pytest_config: PytestConfig) -> Engine:
    db_exists = await async_database_exists(url)
    if db_exists:
        await async_drop_database(url)
    await async_create_database(url)

    engine = create_async_engine(url, echo=pytest_config.getoption("verbose") > 2)  # type: ignore

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine
