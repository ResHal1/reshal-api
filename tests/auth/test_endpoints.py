import pytest
from faker import Faker
from httpx import AsyncClient

from reshal_api.auth.models import UserRole
from reshal_api.config import Config
from tests.factories import UserFactory
from tests.utils import AuthClientFixture

fake = Faker()

app_config = Config()


async def test_users_admin_get(
    admin_client: AuthClientFixture, user_factory: UserFactory
):
    users = user_factory.create_batch(10)

    response = await admin_client.client.get("/auth")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == len(users) + 1
    assert all((str(user.id) in [u["id"] for u in response_data] for user in users))


async def test_token(client: AsyncClient, user_factory: UserFactory):
    user = user_factory.create()

    response = await client.post(
        "/auth/token",
        json={"email": user.email, "password": user_factory._DEFAULT_PASSWORD},
    )
    assert response.status_code == 200

    response_data = response.json()
    cookie = client.cookies.get(app_config.ACCESS_TOKEN_COOKIE_NAME)
    assert cookie is not None

    token_type, token = cookie.split(" ")
    # remove `"` because cookie value is wrapped in `"`
    assert token_type.lower().replace('"', "") == response_data["tokenType"].lower()
    assert token.replace('"', "") == response_data["accessToken"]


async def test_token_invalid_credentials(client: AsyncClient):
    data = {"email": fake.email(), "password": fake.password()}

    response = await client.post("/auth/token", json=data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_register_post(client: AsyncClient, user_factory: UserFactory):
    user = user_factory.build()
    data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user_factory._DEFAULT_PASSWORD,
    }
    response = await client.post("/auth", json=data)
    assert response.status_code == 201

    response_data = response.json()
    assert response_data["email"] == data["email"]
    assert response_data["firstName"] == data["first_name"]
    assert response_data["lastName"] == data["last_name"]
    assert response_data["role"] == UserRole.normal

    response = await client.post(
        "/auth/token", json={"email": user.email, "password": data["password"]}
    )
    assert response.status_code == 200


async def test_register_post_email_exists(
    client: AsyncClient, user_factory: UserFactory
):
    user = user_factory.create()
    data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user_factory._DEFAULT_PASSWORD,
    }

    response = await client.post("/auth", json=data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


async def test_me_get(auth_client: AuthClientFixture):
    response = await auth_client.client.get("/auth/me")
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["id"] == str(auth_client.user.id)
    assert response_data["email"] == auth_client.user.email
    assert response_data["firstName"] == auth_client.user.first_name
    assert response_data["lastName"] == auth_client.user.last_name
    assert response_data["role"] == auth_client.user.role


@pytest.mark.parametrize(
    "data",
    (
        {
            "currentPassword": UserFactory._DEFAULT_PASSWORD,
            "lastName": fake.last_name(),
        },
        {
            "currentPassword": UserFactory._DEFAULT_PASSWORD,
            "firstName": fake.first_name(),
        },
        {
            "currentPassword": UserFactory._DEFAULT_PASSWORD,
            "email": fake.email(),
        },
        {
            "currentPassword": UserFactory._DEFAULT_PASSWORD,
            "email": fake.email(),
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
        },
    ),
)
async def test_me_put(auth_client: AuthClientFixture, data: dict[str, str]):
    response = await auth_client.client.put("/auth/me", json=data)
    assert response.status_code == 200

    response_data = response.json()
    assert all(
        (
            response_data[key] == data[key]
            for key in data.keys()
            if key != "currentPassword"
        )
    )

    response = await auth_client.client.get("/auth/me")
    assert response.status_code == 200
    response_data = response.json()
    assert all(
        (
            response_data[key] == data[key]
            for key in data.keys()
            if key != "currentPassword"
        )
    )


async def test_me_put_wrong_password(auth_client: AuthClientFixture):
    response = await auth_client.client.put(
        "/auth/me",
        json={"currentPassword": "wrongPassword12#!@#", "firstName": "new first name"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid password"


async def test_me_put_email_exists(
    auth_client: AuthClientFixture, user_factory: UserFactory
):
    user = user_factory.create()

    response = await auth_client.client.put(
        "/auth/me",
        json={"currentPassword": user_factory._DEFAULT_PASSWORD, "email": user.email},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


async def test_logout(auth_client: AuthClientFixture):
    response = await auth_client.client.get("/auth/logout")
    assert response.status_code == 204
    assert f'{app_config.ACCESS_TOKEN_COOKIE_NAME}=""' in response.headers.get(
        "set-cookie"
    )
    assert response.cookies.get(app_config.ACCESS_TOKEN_COOKIE_NAME) is None

    response = await auth_client.client.get("/auth/me")
    assert response.status_code == 401
