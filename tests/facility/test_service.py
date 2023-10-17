from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.models import User, UserRole
from reshal_api.facility.models import Facility, FacilityImage
from reshal_api.facility.service import FacilityService, FacilityTypeService
from tests.factories import FacilityFactory, FacilityTypeFactory, UserFactory

fake = Faker()


# Facility Type Service


async def test_type_service_type_name_exists(
    db_session: AsyncSession,
    facility_type_service: FacilityTypeService,
    facility_type_factory: FacilityTypeFactory,
):
    type = facility_type_factory.create()
    type_name_exists = await facility_type_service.type_name_exists(
        db_session, type.name
    )

    assert type_name_exists is True


async def test_type_service_type_name_exists_does_not_exist(
    db_session: AsyncSession,
    facility_type_service: FacilityTypeService,
):
    type_name_exists = await facility_type_service.type_name_exists(
        db_session, fake.word()
    )

    assert type_name_exists is False


# Facility Service


async def test_facility_service_get_facilities_by_owner_id(
    db_session: AsyncSession,
    facility_service: FacilityService,
    facility_factory: FacilityFactory,
    user_factory: UserFactory,
):
    user = user_factory.create()

    facilities = facility_factory.create_batch(2, owners=[user])

    facilities_by_owner_id = await facility_service.get_facilities_by_owner_id(
        db_session, user.id
    )
    assert all(
        (
            facility.id in [f.id for f in facilities]
            for facility in facilities_by_owner_id
        )
    )

    user2 = user_factory.create()
    facilities_user2 = await facility_service.get_facilities_by_owner_id(
        db_session, user2.id
    )
    assert facilities_user2 == []


async def test_facility_service_get_facilities_by_type(
    db_session: AsyncSession,
    facility_service: FacilityService,
    facility_type_factory: FacilityTypeFactory,
    facility_factory: FacilityFactory,
):
    f_type = facility_type_factory.create()
    facilities = facility_factory.build_batch(5)
    for f in facilities:
        f.type_id = f_type.id
        db_session.add(f)
    await db_session.flush()

    facilities_by_type = await facility_service.get_facilities_by_type(
        db_session, f_type.id
    )

    assert all(
        (
            facility.id in [f.id for f in facilities_by_type]
            for facility in facilities_by_type
        )
    )


async def test_facility_service_add_owner(
    db_session: AsyncSession,
    user_factory: UserFactory,
    facility_service: FacilityService,
    facility_factory: FacilityFactory,
):
    user = user_factory.create()
    facility = facility_factory.create()

    await facility_service.add_owner(db_session, facility, user)
    await db_session.flush()

    user_from_db = await db_session.get(User, user.id)
    assert user_from_db is not None
    assert user_from_db.role == UserRole.owner

    facility_from_db = await db_session.get(Facility, facility.id)
    assert facility_from_db is not None
    assert user.id in [u.id for u in facility_from_db.owners]


async def test_facility_service_remove_owner(
    db_session: AsyncSession,
    user_factory: UserFactory,
    facility_service: FacilityService,
    facility_factory: FacilityFactory,
):
    user = user_factory.create(role=UserRole.owner)
    facility = facility_factory.create(owners=[user])

    await facility_service.remove_owner(db_session, facility, user)
    await db_session.flush()

    user_from_db = await db_session.get(User, user.id)
    assert user_from_db is not None
    assert user_from_db.role == UserRole.normal

    facility_from_db = await db_session.get(Facility, facility.id)
    assert facility_from_db is not None
    assert user.id not in [u.id for u in facility_from_db.owners]


async def test_facility_service_remove_owner_keep_owner_role_if_remaining_facilities(
    db_session: AsyncSession,
    user_factory: UserFactory,
    facility_service: FacilityService,
    facility_factory: FacilityFactory,
):
    user = user_factory.create(role=UserRole.owner)
    facilities = facility_factory.create_batch(2)

    await facility_service.add_owner(
        session=db_session, facility=facilities[0], user=user
    )
    await facility_service.add_owner(
        session=db_session, facility=facilities[1], user=user
    )
    await db_session.commit()

    await facility_service.remove_owner(db_session, facilities[0], user)
    await db_session.flush()

    user_from_db = await db_session.get(User, user.id)
    assert user_from_db is not None
    assert user_from_db.role == UserRole.owner

    facility_from_db_1 = await db_session.get(Facility, facilities[0].id)
    assert facility_from_db_1 is not None
    assert user.id not in [u.id for u in facility_from_db_1.owners]

    facility_from_db_2 = await db_session.get(Facility, facilities[1].id)
    assert facility_from_db_2 is not None
    assert user.id in [u.id for u in facility_from_db_2.owners]


async def test_facility_service_delete_images_are_removed_on_delete(
    db_session: AsyncSession,
    facility_service: FacilityService,
    facility_factory: FacilityFactory,
):
    facility = facility_factory.create()

    await facility_service.delete(db_session, id=str(facility.id))
    await db_session.commit()

    images_from_db = (
        await db_session.execute(
            select(FacilityImage).where(FacilityImage.facility_id == str(facility.id))
        )
    ).fetchall()

    assert len(images_from_db) == 0
