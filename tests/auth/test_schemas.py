import pytest
from faker import Faker
from pydantic import ValidationError

from reshal_api.auth.schemas import UserCreate, UserUpdate

from ..factories import UserFactory

fake = Faker()
emails_list = (
    *((fake.free_email(), True) for _ in range(5)),
    *(
        (f"{blacklist_value}@reshal.com", False)
        for blacklist_value in (
            "admin",
            "administrator",
            "root",
            "sysadmin",
            "me",
            "sales",
            "info",
            "support",
            "contact",
            "help",
            "feedback",
            "abuse",
            "webmaster",
            "postmaster",
            "noreply",
            "marketing",
            "spam",
        )
    ),
)

schemas = [UserCreate, UserUpdate]


@pytest.mark.parametrize("Schema", schemas)
@pytest.mark.parametrize(
    "email,is_valid",
    emails_list,
)
def test_schemas_email_validation(
    Schema: type[UserCreate | UserUpdate],
    email: str,
    is_valid: bool,
    user_factory: UserFactory,
):
    user = user_factory.build()
    data = {
        "email": email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    if Schema is UserCreate:
        data["password"] = fake.password()

    if Schema is UserUpdate:
        data["current_password"] = fake.password()

    if is_valid:
        try:
            Schema(**data)
        except ValidationError:
            pytest.fail(f"Email {email!r} should be valid")
    else:
        with pytest.raises(ValidationError) as exc_info:
            Schema(**data)

        assert "Email is not allowed" in str(exc_info.value)


@pytest.mark.parametrize("Schema", schemas)
@pytest.mark.parametrize(
    "password,is_valid",
    (
        ("dupa123", False),
        (fake.password(length=5), False),
        (fake.password(length=200), False),
        (fake.password(special_chars=False), False),
        (fake.password(digits=False), False),
    ),
)
def test_schemas_password_complexity(
    Schema: type[UserCreate | UserUpdate],
    password: str,
    is_valid: bool,
    user_factory: UserFactory,
):
    user = user_factory.build()
    data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    if Schema is UserCreate:
        data["password"] = password

    if Schema is UserUpdate:
        data["new_password"] = password
        data["current_password"] = user.password

    if is_valid:
        try:
            Schema(**data)
        except ValidationError:
            pytest.fail(f"Password {password!r} should be valid")
    else:
        with pytest.raises(ValidationError) as exc_info:
            Schema(**data)

        assert "Password must contain" in str(exc_info.value)
