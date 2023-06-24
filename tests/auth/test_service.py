import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.exceptions import InvalidAuthRequest
from reshal_api.auth.schemas import AuthRequest, UserCreate, UserUpdate
from reshal_api.auth.service import AuthService
from tests.factories import UserFactory

fake = Faker()


async def test_create(db_session: AsyncSession, auth_service: AuthService):
    data = UserCreate(
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        password=fake.password(),
    )

    user = await auth_service.create(db_session, create_obj=data)

    user_from_service = await auth_service.get_by_id(db_session, user.id)
    assert user_from_service is not None


@pytest.mark.parametrize(
    "data",
    (
        {"email": fake.email()},
        {"email": fake.email(), "last_name": fake.last_name()},
        UserUpdate(
            current_password="not needed",
            first_name=fake.first_name(),
        ),  # type: ignore
    ),
)
async def test_update(
    db_session: AsyncSession,
    auth_service: AuthService,
    data: dict[str, str] | UserUpdate,
):
    user = UserFactory.create()

    updated_user = await auth_service.update(
        db_session,
        update_obj=data,
        id=user.id,
    )

    if isinstance(data, UserUpdate):
        data = data.dict(exclude_unset=True)
    data_keys = (
        data.keys() if isinstance(data, dict) else data.dict(exclude_unset=True).keys()
    )

    assert all([getattr(updated_user, key) == data[key] for key in data_keys])


async def test_get_by_email(
    db_session: AsyncSession, auth_service: AuthService, user_factory: UserFactory
):
    user = user_factory.create()
    user_from_service = await auth_service.get_by_email(db_session, user.email)

    assert user_from_service is not None
    assert user_from_service.id == user.id


async def test_get_by_email_does_not_exist(
    db_session: AsyncSession, auth_service: AuthService
):
    user_from_service = await auth_service.get_by_email(db_session, "wrong email")
    assert user_from_service is None


async def test_get_by_id(
    db_session: AsyncSession, auth_service: AuthService, user_factory: UserFactory
):
    user = user_factory.create()
    user_from_service = await auth_service.get_by_id(db_session, user.id)
    assert user_from_service is not None
    assert user_from_service.id == user.id


async def test_get_by_id_does_not_exist(
    db_session: AsyncSession, auth_service: AuthService
):
    import uuid

    user_from_service = await auth_service.get_by_id(db_session, uuid.uuid4())
    assert user_from_service is None


@pytest.mark.parametrize(
    "password,is_valid",
    (
        (UserFactory._DEFAULT_PASSWORD, True),
        ("wrongPassword", False),
    ),
)
async def test_is_password_valid(
    auth_service: AuthService,
    user_factory: UserFactory,
    password: str,
    is_valid: bool,
):
    user = user_factory.create()
    is_password_valid_service = await auth_service.is_password_valid(user, password)

    assert is_password_valid_service == is_valid


async def test_authenticate_user(
    db_session: AsyncSession, auth_service: AuthService, user_factory: UserFactory
):
    user = user_factory.create()
    authenticated_user = await auth_service.authenticate_user(
        db_session,
        AuthRequest(email=user.email, password=user_factory._DEFAULT_PASSWORD),
    )
    assert authenticated_user.id == user.id


async def test_authenticate_user_user_does_not_exist(
    db_session: AsyncSession, auth_service: AuthService, user_factory: UserFactory
):
    with pytest.raises(InvalidAuthRequest):
        await auth_service.authenticate_user(
            db_session,
            AuthRequest(email=fake.email(), password=user_factory._DEFAULT_PASSWORD),
        )


async def test_authenticate_user_invalid_password(
    db_session: AsyncSession, auth_service: AuthService, user_factory: UserFactory
):
    user = user_factory.create()

    with pytest.raises(InvalidAuthRequest):
        await auth_service.authenticate_user(
            db_session,
            AuthRequest(email=user.email, password="invalidPassword"),
        )
