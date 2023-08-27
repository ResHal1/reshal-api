from datetime import timedelta

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from faker.providers import BaseProvider, ElementsType
from pytz import UTC

from reshal_api.auth import security
from reshal_api.auth.models import User, UserRole
from reshal_api.facility.models import Facility, FacilityType
from reshal_api.payment.models import Payment, PaymentStatus
from reshal_api.reservation.models import Reservation

from .database import scoped_session_local

fake = Faker()


class FacilityTypeProvider(BaseProvider):
    types: ElementsType[str] = [
        "Gymnasium",
        "Sports complex",
        "Stadium",
        "Indoor arena",
        "Outdoor field",
        "Tennis court",
        "Basketball court",
        "Football field",
        "Swimming pool",
        "Ice rink",
        "Golf course",
        "Cricket ground",
        "Baseball diamond",
        "Volleyball court",
        "Badminton court",
        "Squash court",
        "Track and field facility",
        "Skate park",
        "Bowling alley",
        "Martial arts studio",
        "Yoga studio",
        "Climbing gym",
        "Cycling velodrome",
        "Archery range",
        "Fitness center",
        "Multi-purpose sports hall",
        "Water sports center",
        "Skateboarding park",
    ]

    def facility_type(self) -> str:
        return self.random_element(self.types)


fake.add_provider(FacilityTypeProvider)


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = scoped_session_local
        sqlalchemy_session_persistence = "commit"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        cls._meta.sqlalchemy_session.expire(instance)
        return instance


# class TimestampFactory(BaseFactory):
#     created_at = FuzzyDateTime(start_dt=datetime.now(tz=UTC))
#     updated_at = FuzzyDateTime(start_dt=datetime.now(tz=UTC))


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

    # FIXME: Params
    @classmethod
    def _create(cls, model_class, *args, session=None, **kwargs):
        if factory_custom_password := kwargs.get("custom_password"):
            kwargs["password"] = security.hash_password(factory_custom_password)
        return super()._create(model_class, *args, **kwargs)


class FacilityTypeFactory(BaseFactory):
    class Meta:
        model = FacilityType

    name = factory.Sequence(lambda n: f"{fake.facility_type()}{n}")


class ReservationFactory(BaseFactory):
    class Meta:
        model = Reservation

    start_time = factory.Faker(
        "date_time_this_year", before_now=False, after_now=True, tzinfo=UTC
    )
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(hours=1))
    price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    user_id = factory.LazyAttribute(lambda _: UserFactory.create().id)

    # @factory.post_generation
    # def facility(self, create, extracted, **kwargs):
    #     if not create:
    #         return

    #     if extracted:
    #         self.facility = extracted
    #         self.facility_id = extracted.id

    # @factory.post_generation
    # def payment(self, create, extracted, **kwargs):
    #     if not create:
    #         return

    #     if extracted:
    #         self.payment = extracted
    #         self.payment_id = extracted.id


class FacilityFactory(BaseFactory):
    class Meta:
        model = Facility

    name = factory.Faker("company")
    description = factory.Faker("text")
    lat = factory.Faker("latitude")
    lon = factory.Faker("longitude")
    # lat = factory.LazyAttribute(lambda: fake.local_latlng(country_code="PL")[0])
    # lon = factory.LazyAttribute(lambda: fake.local_latlng(country_code="PL")[1])
    image_url = factory.Faker("url")
    price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    address = factory.Faker("address", locale="pl_PL")

    type = factory.SubFactory(FacilityTypeFactory)

    @factory.post_generation
    def owners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for owner in extracted:
                self.owners.append(owner)  # type: ignore

    @factory.post_generation
    def reservations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for reservation in extracted:
                self.revervations.append(reservation)  # type: ignore


class PaymentFactory(BaseFactory):
    class Meta:
        model = Payment

    status = PaymentStatus.paid  # FIXME: this is set to paid everywhere for now
    price = factory.LazyAttribute(
        lambda obj: fake.pydecimal(left_digits=2, right_digits=2, positive=True)
    )

    @factory.post_generation
    def reservation_id(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.reservation_id = extracted
