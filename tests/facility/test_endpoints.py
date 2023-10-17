import humps
import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.models import UserRole
from reshal_api.auth.service import AuthService
from reshal_api.facility.models import Facility, FacilityType
from reshal_api.facility.schemas import FacilityCreate, FacilityReadAdmin
from tests.database import scoped_session_local
from tests.factories import (
    FacilityFactory,
    FacilityTypeFactory,
    PaymentFactory,
    ReservationFactory,
    UserFactory,
)
from tests.utils import AuthClientFixture, authenticate_client

fake = Faker()

# Facility Type Endpoints


async def test_facility_type_get_all(
    client: AsyncClient, facility_type_factory: FacilityTypeFactory
):
    types = facility_type_factory.create_batch(10)

    response = await client.get("/facilities/types")
    assert response.status_code == 200

    response_data = response.json()
    assert all(
        (str(f_type.id) in [ft["id"] for ft in response_data] for f_type in types)
    )


async def test_facility_type_create(
    admin_client: AuthClientFixture, facility_type_factory: FacilityTypeFactory
):
    f_type = facility_type_factory.build()
    data = {"name": f_type.name}

    response = await admin_client.client.post("/facilities/types", json=data)
    assert response.status_code == 201
    assert response.json()["name"] == f_type.name


async def test_facility_type_create_name_exists_conflict(
    admin_client: AuthClientFixture, facility_type_factory: FacilityTypeFactory
):
    f_type = facility_type_factory.create()
    data = {"name": f_type.name}

    response = await admin_client.client.post("/facilities/types", json=data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == f"Facility type {data['name']!r} already exists"


async def test_facility_type_create_unauthorized(
    auth_client: AuthClientFixture, facility_type_factory: FacilityTypeFactory
):
    f_type = facility_type_factory.build()
    data = {"name": f_type.name}

    response = await auth_client.client.post("/facilities/types", json=data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied"


async def test_facility_type_delete(
    admin_client: AuthClientFixture, facility_type_factory: FacilityTypeFactory
):
    f_type = facility_type_factory.create()
    response = await admin_client.client.get("/facilities/types")
    assert response.status_code == 200

    response = await admin_client.client.delete(f"/facilities/types/{str(f_type.id)}")
    assert response.status_code == 204

    response = await admin_client.client.get("/facilities/types")
    assert str(f_type.id) not in response.json()


async def test_facility_type_delete_unauthorized(
    client: AsyncClient, facility_type_factory: FacilityTypeFactory
):
    f_type = facility_type_factory.create()
    response = await client.delete(f"/facilities/types/{str(f_type.id)}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# Facility Endpoints


async def test_facility_get_all(client: AsyncClient, facility_factory: FacilityFactory):
    facilities = facility_factory.create_batch(5)

    response = await client.get("/facilities")
    assert response.status_code == 200
    assert all(
        (
            str(facility.id) in [f["id"] for f in response.json()]
            for facility in facilities
        )
    )


async def test_facility_get_by_id(
    client: AsyncClient, facility_factory: FacilityFactory
):
    facility = facility_factory.create()

    response = await client.get(f"/facilities/{str(facility.id)}")
    assert response.status_code == 200
    assert response.json()["id"] == str(facility.id)


async def test_create_facility(
    admin_client: AuthClientFixture,
    facility_type_factory: FacilityTypeFactory,
    facility_factory: FacilityFactory,
):
    facility_type = facility_type_factory.create()
    facility = facility_factory.build()

    # Using schema bcs of decimal
    data = FacilityCreate(
        name=facility.name,
        description=facility.description,
        lat=facility.lat,
        lon=facility.lon,
        address=facility.address,
        price="10.00",
        images=facility.images,
        type_id=facility_type.id,
    )
    data_dict = data.dict()

    response = await admin_client.client.post(
        "/facilities", headers={"Content-Type": "application/json"}, content=data.json()
    )
    assert response.status_code == 201

    response_data = response.json()

    assert response_data["price"] == str(data.price)
    assert all(
        (
            response_data[key] == data_dict[key]
            for key in [
                "name",
                "description",
                "lat",
                "lon",
                "address",
            ]
        )
    )
    assert all(
        [
            image["url"] in [img.path for img in data.images]
            for image in response_data["images"]
        ]
    )
    assert response_data["type"]["id"] == str(facility_type.id)
    assert response_data["type"]["name"] == facility_type.name

    response = await admin_client.client.get(f"/facilities/{response_data['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == response_data["id"]


async def test_get_all_admin(
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
    user_factory: UserFactory,
):
    user = user_factory.create()
    facilities = facility_factory.create_batch(2, owners=[admin_client.user, user])

    response = await admin_client.client.get("/facilities/admin")
    assert response.status_code == 200

    response_data = response.json()
    for facility in facilities:
        facility_from_response = list(
            filter(lambda f: f["id"] == str(facility.id), response_data)
        )[0]
        expected = FacilityReadAdmin.from_orm(facility).dict()

        assert all(
            (
                facility_from_response[humps.camelize(key)] == expected[key]
                for key in [
                    "name",
                    "description",
                    "lat",
                    "lon",
                    "address",
                ]
            )
        )
        assert all(
            (
                owner["id"] in [str(admin_client.user.id), str(user.id)]
                for owner in facility_from_response["owners"]
            )
        )
        assert all(
            [
                image["url"] in [img.path for img in facility.images]
                for image in facility_from_response["images"]
            ]
        )
        assert facility_from_response["type"]["id"] == str(facility.type_id)
        assert facility_from_response["type"]["name"] == facility.type.name
        assert facility_from_response["price"] == str(facility.price)


async def test_facilities_list_me(
    client: AsyncClient, facility_factory: FacilityFactory, user_factory: UserFactory
):
    user = user_factory.create(role=UserRole.owner)
    facilities = facility_factory.create_batch(3, owners=[user])
    scoped_session_local.commit()  # FIXME:

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)
    response = await client.get("/facilities/me")
    print(f"Facilities response: {len(response.json())}")
    assert response.status_code == 200
    assert all(
        (
            str(facility.id) in [f["id"] for f in response.json()]
            for facility in facilities
        )
    )


async def test_assign_ownership(
    db_session: AsyncSession,
    auth_service: AuthService,
    client: AsyncClient,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
    user_factory: UserFactory,
):
    user = user_factory.create(role=UserRole.owner)
    facility = facility_factory.create()

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)

    response = await client.get("/facilities/me")
    assert response.status_code == 200
    assert response.json() == []

    data = {"userId": str(user.id), "facilityId": str(facility.id)}
    response = await admin_client.client.post("/facilities/assign-ownership", json=data)
    assert response.status_code == 200

    response = await client.get("/facilities/me")
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(facility.id)

    user = await auth_service.get_by_id(db_session, user.id)
    assert user is not None
    assert user.role == UserRole.owner


async def test_revoke_ownership(
    db_session: AsyncSession,
    client: AsyncClient,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
    user_factory: UserFactory,
    auth_service: AuthService,
):
    user = user_factory.create(role=UserRole.owner)
    facility = facility_factory.create(owners=[user])
    scoped_session_local.commit()

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)
    response = await client.get("/facilities/me")
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(facility.id)

    data = {"userId": str(user.id), "facilityId": str(facility.id)}
    response = await admin_client.client.request(
        "DELETE", "/facilities/revoke-ownership", json=data
    )
    assert response.status_code == 200

    response = await client.get("/facilities/me")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not an owner"

    user = await auth_service.get_by_id(db_session, user.id)
    assert user is not None
    assert user.role == UserRole.normal


async def test_reservations_for_facility(
    client: AsyncClient,
    facility_factory: FacilityFactory,
    reservation_factory: ReservationFactory,
    payment_factory: PaymentFactory,
):
    facility = facility_factory.create()
    payment = payment_factory.create()
    reservations = reservation_factory.create_batch(
        5,
        facility_id=facility.id,
        payment_id=payment.id,
    )

    response = await client.get(f"/facilities/{facility.id}/reservations")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) > 0
    assert all(
        (
            reservation["id"] in [str(r.id) for r in reservations]
            for reservation in response_data
        )
    )


async def test_get_facility_by_id(
    admin_client: AuthClientFixture, facility_factory: FacilityFactory
):
    facility = facility_factory.create()

    response = await admin_client.client.get(f"/facilities/{facility.id}")
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["id"] == str(facility.id)


@pytest.mark.parametrize(
    "update_data",
    [
        {
            "name": "New Name",
            "description": "New Description",
            "lat": 70.12,
            "lon": 12.12,
            "address": fake.address(),
            "price": "10.12",
            "images": [{"url": fake.url()}],
        },
        {
            "lat": 70.12,
            "lon": 12.12,
            "price": "10.12",
        },
        {
            "images": [{"url": fake.url()} for _ in range(10)],
        },
        {
            "price": "21.21",
        },
        {},
    ],
)
async def test_facility_put(
    update_data: dict,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
):
    facility = facility_factory.create()

    response = await admin_client.client.put(
        f"/facilities/{str(facility.id)}", json=update_data
    )
    assert response.status_code == 200

    response_data = response.json()
    assert all([response_data[key] == update_data[key] for key in update_data.keys()])


async def test_facility_delete(
    admin_client: AuthClientFixture, facility_factory: FacilityFactory
):
    facility = facility_factory.create()

    response = await admin_client.client.delete(f"/facilities/{str(facility.id)}")
    assert response.status_code == 204

    response = await admin_client.client.get(f"/facilities/{str(facility.id)}")
    assert response.status_code == 404
