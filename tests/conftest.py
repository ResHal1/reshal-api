import asyncio

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from reshal_api.auth.models import UserRole
from reshal_api.auth.service import AuthService
from reshal_api.config import DatabaseSettings
from reshal_api.database import Base
from reshal_api.main import app
from tests.factories import UserFactory
from tests.utils import (
    AuthClientFixture,
    create_database,
    database_exists,
    drop_database,
)


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine(pytestconfig):
    db_config = DatabaseSettings()

    assert db_config.NAME.endswith(
        "test"
    )  # check if production/local database is used by mistake

    db_exists = await database_exists(db_config.url)
    if db_exists:
        await drop_database(db_config.url)
    await create_database(db_config.url)

    test_engine = create_async_engine(
        db_config.url, echo=pytestconfig.getoption("verbose") > 2
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    await drop_database(db_config.url)
    await test_engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def db_session(engine: AsyncEngine):
    async with engine.connect() as conn:
        async with conn.begin():
            session = AsyncSession(conn)
            yield session
            await session.rollback()
            await session.close()


@pytest.fixture()
async def client(db_session: AsyncSession):
    app.dependency_overrides[AsyncSession] = lambda: db_session

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture()
async def auth_client(client: httpx.AsyncClient, user_factory: UserFactory):
    user = UserFactory.create()
    data = {"email": user.email, "password": user_factory._DEFAULT_PASSWORD}

    response = await client.post("/auth/token", json=data)
    assert response.status_code == 200

    return AuthClientFixture(client=client, user=user)


@pytest.fixture()
async def admin_client(client: httpx.AsyncClient, user_factory: UserFactory):
    admin_user = UserFactory.create(role=UserRole.admin)
    data = {"email": admin_user.email, "password": user_factory._DEFAULT_PASSWORD}

    response = await client.post("/auth/token", json=data)
    assert response.status_code == 200

    return AuthClientFixture(client=client, user=admin_user)


# Services


@pytest.fixture()
def auth_service():
    return AuthService()


# Factories


@pytest.fixture()
def user_factory():
    return UserFactory
