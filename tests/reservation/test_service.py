from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.reservation.service import ReservationService
from tests.factories import FacilityFactory, PaymentFactory, ReservationFactory

BASE_DT = datetime.now(tz=pytz.timezone("UTC")) + timedelta(days=1)
OVERLAPPING_START_TIME = BASE_DT + timedelta(minutes=30)
OVERLAPPING_END_TIME = OVERLAPPING_START_TIME + timedelta(hours=1)


@pytest.mark.parametrize(
    "start_time, end_time, is_overlapping",
    (
        (
            OVERLAPPING_START_TIME + timedelta(days=2),
            OVERLAPPING_START_TIME + timedelta(days=2, hours=1),
            False,
        ),
        (OVERLAPPING_START_TIME, OVERLAPPING_START_TIME + timedelta(hours=1), True),
    ),
)
async def test_service_is_overlapping(
    start_time: datetime,
    end_time: datetime,
    is_overlapping: bool,
    db_session: AsyncSession,
    reservation_service: ReservationService,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    facility = facility_factory.create()
    payment = payment_factory.create()
    reservation_factory.create(
        start_time=OVERLAPPING_START_TIME,
        end_time=OVERLAPPING_END_TIME,
        facility_id=facility.id,
        payment_id=payment.id,
    )

    result = await reservation_service.is_overlapping(
        db_session, facility.id, start_time, end_time
    )

    assert result == is_overlapping


# FIXME: flaky
async def test_service_get_all_in_timeframe(
    db_session: AsyncSession,
    reservation_service: ReservationService,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    BASE_DT2 = BASE_DT + timedelta(days=30)
    facility = facility_factory.create()
    target = [BASE_DT2 + timedelta(hours=i) for i in range(0, 20, 2)]

    for _ in range(10):
        payment = payment_factory.create()
        reservation_factory.create(facility_id=facility.id, payment_id=payment.id)

    target_reservations = []

    for start_time in target:
        payment = payment_factory.create()
        reservation = reservation_factory.create(
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            facility_id=facility.id,
            payment_id=payment.id,
        )
        target_reservations.append(reservation)

    result = await reservation_service.get_all_in_timeframe(
        db_session, target_reservations[0].start_time, target_reservations[-1].end_time
    )

    assert all(
        (
            reservation.id in [tr.id for tr in target_reservations]
            for reservation in result
        )
    )

    result2 = await reservation_service.get_all_in_timeframe(
        db_session,
        datetime.now() - timedelta(days=70),
        datetime.now() - timedelta(days=60),
    )

    assert result2 == []


@pytest.mark.parametrize(
    "end_time_timedelta,facility_price,expected_total_price",
    (
        (
            timedelta(hours=1),
            Decimal(10.0),
            Decimal(10.0),
        ),
        (
            timedelta(hours=1, minutes=5),
            Decimal(10.0),
            Decimal(20.0),
        ),
        (
            timedelta(hours=2, minutes=5),
            Decimal(10.50),
            Decimal(31.50),
        ),
    ),
)
def test_service_calculate_price(
    end_time_timedelta: timedelta,
    facility_price: Decimal,
    expected_total_price: Decimal,
    reservation_service: ReservationService,
):
    start_time = datetime.now()
    end_time = start_time + end_time_timedelta
    result = reservation_service.calcualte_price(facility_price, start_time, end_time)

    assert result == expected_total_price


@pytest.mark.parametrize(
    "reservation_start,expected",
    (
        (BASE_DT + timedelta(hours=1), True),
        (BASE_DT + timedelta(days=-10), False),
    ),
)
async def test_reservations_in_future_exist(
    reservation_start: datetime,
    expected: bool,
    db_session: AsyncSession,
    reservation_service: ReservationService,
    facility_factory: FacilityFactory,
    payment_factory: PaymentFactory,
    reservation_factory: ReservationFactory,
):
    facility = facility_factory.create()
    payment = payment_factory.create()
    reservation_factory.create(
        start_time=reservation_start,
        end_time=reservation_start + timedelta(hours=1),
        facility_id=facility.id,
        payment_id=payment.id,
    )

    result = await reservation_service.reservations_in_future_exist(
        db_session, facility.id
    )
    assert result == expected
