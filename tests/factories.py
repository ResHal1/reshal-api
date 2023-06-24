from datetime import datetime

import factory
from factory.fuzzy import FuzzyDateTime
from pytz import UTC

from reshal_api.auth import security
from reshal_api.auth.models import User, UserRole

from .database import scoped_session_local


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = scoped_session_local
        sqlalchemy_session_persistence = "commit"


class TimestampFactory(BaseFactory):
    created_at = FuzzyDateTime(start_dt=datetime.now(tz=UTC))
    updated_at = FuzzyDateTime(start_dt=datetime.now(tz=UTC))


class UserFactory(BaseFactory):
    _DEFAULT_PASSWORD = "Passw0rd123!@#"
    custom_password = None

    class Meta:
        model = User
        exclude = ("custom_password",)

    email = factory.Faker("email")
    password = factory.LazyAttribute(
        lambda obj: security.hash_password(
            obj.custom_password
            if obj.custom_password is not None
            else UserFactory._DEFAULT_PASSWORD
        )
    )
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = UserRole.normal

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if factory_custom_password := kwargs.get("custom_password"):
            kwargs["password"] = security.hash_password(factory_custom_password)
        return super()._create(model_class, *args, **kwargs)
