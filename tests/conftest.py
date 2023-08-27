import asyncio

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy_utils import create_database, database_exists, drop_database

from reshal_api.auth.models import UserRole
from reshal_api.auth.service import AuthService
from reshal_api.config import DatabaseSettings
from reshal_api.database import Base
from reshal_api.facility.service import FacilityService, FacilityTypeService
from reshal_api.main import app
from reshal_api.reservation.service import ReservationService
from tests.factories import (
    FacilityFactory,
    FacilityTypeFactory,
    PaymentFactory,
    ReservationFactory,
    UserFactory,
)
from tests.utils import (
    AuthClientFixture,
    async_create_database,
    async_database_exists,
    async_drop_database,
    authenticate_client,
)


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_engine(pytestconfig):
    db_config = DatabaseSettings()
    db_config.DRIVER = "psycopg2"

    assert db_config.NAME.endswith("test")

    db_exists = database_exists(db_config.url)
    if db_exists:
        drop_database(db_config.url)
    create_database(db_config.url)

    engine = create_engine(db_config.url)

    with engine.begin() as conn:
        Base.metadata.create_all(conn)

    yield engine

    drop_database(db_config.url)
    engine.dispose()


@pytest.fixture(scope="session")
async def async_engine(pytestconfig):
    db_config = DatabaseSettings()

    assert db_config.NAME.endswith("test")

    db_exists = await async_database_exists(db_config.url)
    if db_exists:
        await async_drop_database(db_config.url)
    await async_create_database(db_config.url)

    engine = create_async_engine(
        db_config.url, echo=pytestconfig.getoption("verbose") > 2
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await async_drop_database(db_config.url)
    await engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def db_session(async_engine: AsyncEngine):
    async with async_engine.connect() as conn:
        async with conn.begin():
            session = AsyncSession(conn)
            yield session
            await session.rollback()
            await session.close()


@pytest.fixture(autouse=True)
def session_override(db_session: AsyncSession):
    app.dependency_overrides[AsyncSession] = lambda: db_session


@pytest.fixture()
async def client():
    app.dependency_overrides[AsyncSession] = lambda: db_session

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture()
async def auth_client(user_factory: UserFactory):
    user = user_factory.create()

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        await authenticate_client(client, user.email, user_factory._DEFAULT_PASSWORD)
        yield AuthClientFixture(client=client, user=user)


@pytest.fixture()
async def admin_client(user_factory: UserFactory):
    admin_user = user_factory.create(role=UserRole.admin)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        await authenticate_client(
            client, admin_user.email, user_factory._DEFAULT_PASSWORD
        )
        yield AuthClientFixture(client=client, user=admin_user)


# Services


@pytest.fixture()
def auth_service():
    return AuthService()


@pytest.fixture()
def facility_type_service():
    return FacilityTypeService()


@pytest.fixture()
def facility_service():
    return FacilityService()


@pytest.fixture()
def reservation_service():
    return ReservationService()


# Factories


@pytest.fixture()
def user_factory():
    return UserFactory


@pytest.fixture()
def facility_type_factory():
    return FacilityTypeFactory


@pytest.fixture()
def facility_factory():
    return FacilityFactory


@pytest.fixture()
def reservation_factory():
    return ReservationFactory


@pytest.fixture()
def payment_factory():
    return PaymentFactory
