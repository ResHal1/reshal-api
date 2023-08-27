from datetime import datetime, timedelta

import pytest
import pytz
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from reshal_api.facility.service import FacilityService
from reshal_api.payment.service import PaymentService
from reshal_api.reservation.models import Reservation
from reshal_api.reservation.service import ReservationService
from tests.factories import (
    FacilityFactory,
    PaymentFactory,
    ReservationFactory,
    UserFactory,
)
from tests.utils import AuthClientFixture, authenticate_client

BASE_DT = datetime.now(tz=pytz.timezone("UTC")) + timedelta(days=1)


async def test_get_all(
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    facility = facility_factory.create()
    reservations = [
        reservation_factory.create(
            facility_id=facility.id,
            payment_id=payment_factory.create().id,
            start_time=BASE_DT + timedelta(days=i),
            end_time=BASE_DT + timedelta(days=i, hours=1),
        )
        for i in range(5)
    ]

    response = await admin_client.client.get(
        "/reservations",
        params={
            "startTime": BASE_DT.isoformat(),
            "endTime": reservations[-1].end_time.isoformat(),
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert all(
        (str(reservation.id) in [r["id"] for r in data] for reservation in reservations)
    )


# default startTime: datetime.now()
# default endTime: datetime.now() + timedelta(weeks=4)
async def test_get_all_default_query_params(
    db_session: AsyncSession,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    facility = facility_factory.create()
    reservations = [
        reservation_factory.create(
            facility_id=facility.id,
            payment_id=payment_factory.create().id,
            start_time=BASE_DT + timedelta(days=i),
            end_time=BASE_DT + timedelta(days=i, hours=1),
        )
        for i in range(5)
    ]

    reservations = (
        (
            await db_session.execute(
                select(Reservation)
                .filter(Reservation.start_time >= BASE_DT)
                .filter(Reservation.end_time <= BASE_DT + timedelta(weeks=4))
            )
        )
        .scalars()
        .all()
    )

    response = await admin_client.client.get("/reservations")
    assert response.status_code == 200

    data = response.json()
    assert all(
        (str(reservation.id) in [r["id"] for r in data] for reservation in reservations)
    )


async def test_create(
    db_session: AsyncSession,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
):
    facility = facility_factory.create()

    start_time = BASE_DT + timedelta(days=21)
    end_time = start_time + timedelta(hours=2)
    data = {
        "facilityId": str(facility.id),
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
    }

    response = await admin_client.client.post("/reservations", json=data)
    assert response.status_code == 201

    data = response.json()

    reservation = await db_session.execute(select(Reservation).filter_by(id=data["id"]))
    assert reservation


async def test_create_reservation_length_too_short(
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
):
    facility = facility_factory.create()

    start_time = BASE_DT + timedelta(minutes=10)
    end_time = start_time + timedelta(minutes=10)
    data = {
        "facilityId": str(facility.id),
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
    }

    response = await admin_client.client.post("/reservations", json=data)
    assert response.status_code == 422

    data = response.json()
    assert data["detail"][0]["msg"] == "Reservation must be at least 30 minutes long."


async def test_create_reservation_length_too_long(
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
):
    facility = facility_factory.create()

    start_time = BASE_DT + timedelta(minutes=10)
    end_time = start_time + timedelta(days=2)
    data = {
        "facilityId": str(facility.id),
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
    }

    response = await admin_client.client.post("/reservations", json=data)
    assert response.status_code == 422

    data = response.json()
    assert data["detail"][0]["msg"] == "Reservation must not be longer than 24 hours."


async def test_create_reservation_price(
    db_session: AsyncSession,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
):
    facility = facility_factory.create()

    start_time = BASE_DT + timedelta(days=21)
    end_time = start_time + timedelta(hours=2)
    data = {
        "facilityId": str(facility.id),
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
    }

    response = await admin_client.client.post("/reservations", json=data)
    assert response.status_code == 201

    data = response.json()


async def test_me(
    client: AsyncClient,
    user_factory: UserFactory,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    user = user_factory.create()
    facility = facility_factory.create()
    reservations = [
        reservation_factory.create(
            user_id=user.id,
            facility_id=facility.id,
            payment_id=payment_factory.create().id,
            start_time=BASE_DT + timedelta(days=i),
            end_time=BASE_DT + timedelta(days=i, hours=1),
        )
        for i in range(3)
    ]

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)

    response = await client.get(
        "/reservations/me",
        params={
            "startTime": reservations[0].start_time.isoformat(),
            "endTime": reservations[-1].end_time.isoformat(),
        },
    )
    assert response.status_code == 200

    data = response.json()

    assert all(
        (str(reservation.id) in [r["id"] for r in data] for reservation in reservations)
    )


async def test_reservation_by_id(
    client: AsyncClient,
    user_factory: UserFactory,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    user = user_factory.create()
    facility = facility_factory.create()
    reservation = reservation_factory.create(
        user_id=str(user.id),
        facility_id=facility.id,
        payment_id=payment_factory.create().id,
    )

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)

    response = await client.get(f"/reservations/{str(reservation.id)}")
    assert response.status_code == 200
    assert response.json()["id"] == str(reservation.id)


async def test_reservation_by_id_forbidden(
    client: AsyncClient,
    user_factory: UserFactory,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    user = user_factory.create()
    facility = facility_factory.create()
    reservation = reservation_factory.create(
        facility_id=facility.id, payment_id=payment_factory.create().id
    )

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)

    response = await client.get(f"/reservations/{str(reservation.id)}")
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied"


async def test_delete(
    db_session: AsyncSession,
    client: AsyncClient,
    user_factory: UserFactory,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    user = user_factory.create()
    facility = facility_factory.create()
    reservation = reservation_factory.create(
        user_id=user.id, facility_id=facility.id, payment_id=payment_factory.create().id
    )

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)
    response = await client.delete(f"/reservations/{str(reservation.id)}")
    assert response.status_code == 204

    r = await db_session.execute(select(Reservation).filter_by(id=reservation.id))
    assert r.scalar_one_or_none() is None


async def test_delete_admin_able_to_delete(
    db_session: AsyncSession,
    admin_client: AuthClientFixture,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    facility = facility_factory.create()
    reservation = reservation_factory.create(
        facility_id=facility.id, payment_id=payment_factory.create().id
    )

    response = await admin_client.client.delete(f"/reservations/{str(reservation.id)}")
    assert response.status_code == 204

    r = await db_session.execute(select(Reservation).filter_by(id=reservation.id))
    assert r.scalar_one_or_none() is None


async def test_delete_forbidden(
    db_session: AsyncSession,
    client: AsyncClient,
    user_factory: UserFactory,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    user = user_factory.create()
    facility = facility_factory.create()
    reservation = reservation_factory.create(
        facility_id=facility.id, payment_id=payment_factory.create().id
    )

    await authenticate_client(client, user.email, UserFactory._DEFAULT_PASSWORD)

    response = await client.delete(f"/reservations/{str(reservation.id)}")
    assert response.status_code == 204

    r = await db_session.execute(select(Reservation).filter_by(id=reservation.id))
    assert r.scalar_one_or_none() is not None
