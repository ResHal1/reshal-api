import uuid
from datetime import datetime, timedelta

import pytest
import pytz
from faker import Faker

from reshal_api.reservation.schemas import ReservationCreate, ReservationCreateBase

fake = Faker()


def test_reservation_start_time_validators():
    start_time = datetime.now() + timedelta(minutes=1)
    end_time = start_time + timedelta(minutes=45)

    data = {
        "facility_id": str(uuid.uuid4()),
        "start_time": start_time,
        "end_time": end_time,
    }

    reservation = ReservationCreateBase(**data)
    assert reservation

    with pytest.raises(ValueError):
        start_time_invalid = datetime.now() + timedelta(minutes=-10)
        end_time_invalid = start_time
        data2 = {
            "facility_id": str(uuid.uuid4()),
            "start_time": start_time_invalid,
            "end_time": end_time_invalid,
        }
        ReservationCreateBase(**data2)


def test_reservation_end_time_validators():
    start_time = datetime.now() + timedelta(minutes=1)
    end_time = start_time + timedelta(minutes=45)

    data = {
        "facility_id": str(uuid.uuid4()),
        "start_time": start_time,
        "end_time": end_time,
    }

    reservation = ReservationCreateBase(**data)
    assert reservation

    with pytest.raises(ValueError):
        end_time_invalid = start_time + timedelta(minutes=-10)
        data2 = {
            "facility_id": str(uuid.uuid4()),
            "start_time": start_time,
            "end_time": end_time_invalid,
        }
        ReservationCreateBase(**data2)


@pytest.mark.parametrize(
    "end_time_timedelta,is_valid",
    (
        (timedelta(minutes=30), True),
        (timedelta(hours=24), True),
        (timedelta(hours=1), True),
        (timedelta(minutes=10), False),
        (timedelta(minutes=1), False),
    ),
)
def test_reservation_duration_is_atleast_30_min_validator(
    end_time_timedelta: timedelta, is_valid: bool
):
    start_time = datetime.now() + timedelta(minutes=1)
    end_time = start_time + end_time_timedelta
    data = {
        "facility_id": str(uuid.uuid4()),
        "start_time": start_time,
        "end_time": end_time,
    }

    if is_valid:
        try:
            reservation = ReservationCreateBase(**data)
            assert reservation
        except ValueError:
            pytest.fail("Reservation is least 30 minutes long.")
    else:
        with pytest.raises(ValueError) as exc_info:
            ReservationCreateBase(**data)
        assert "Reservation must be at least 30 minutes long." in str(exc_info.value)


@pytest.mark.parametrize(
    "end_time_timedelta,is_valid",
    (
        (timedelta(minutes=30), True),
        (timedelta(hours=12), True),
        (timedelta(hours=23), True),
        (timedelta(hours=25), False),
        (timedelta(days=2), False),
    ),
)
def test_reservation_duration_is_less_than_24_hours_validator(
    end_time_timedelta: timedelta, is_valid: bool
):
    start_time = datetime.now() + timedelta(minutes=1)
    end_time = start_time + end_time_timedelta
    data = {
        "facility_id": str(uuid.uuid4()),
        "start_time": start_time,
        "end_time": end_time,
    }

    if is_valid:
        try:
            reservation = ReservationCreateBase(**data)
            assert reservation
        except ValueError:
            pytest.fail("Reservation is less than 24 hours long.")
    else:
        with pytest.raises(ValueError) as exc_info:
            ReservationCreateBase(**data)
        assert "Reservation must not be longer than 24 hours." in str(exc_info.value)


@pytest.mark.parametrize(
    "start_time,is_valid",
    (
        (datetime.now() + timedelta(minutes=5), True),
        (datetime.now(tz=pytz.timezone("Europe/Warsaw")) + timedelta(hours=1), True),
        (datetime.now(), False),
        (datetime.now() + timedelta(minutes=-1), False),
    ),
)
def test_reservation_create_test_start_time_validator(
    start_time: datetime, is_valid: bool
):
    data = {
        "facility_id": str(uuid.uuid4()),
        "payment_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "start_time": start_time,
        "end_time": start_time + timedelta(minutes=30),
        "price": fake.pydecimal(left_digits=2, right_digits=2, positive=True),
    }

    if is_valid:
        try:
            reservation = ReservationCreate(**data)
            assert reservation.start_time.tzinfo == pytz.timezone("UTC")
        except ValueError:
            pytest.fail(f"Start time {start_time!r} should be valid")
    else:
        with pytest.raises(ValueError) as exc_info:
            ReservationCreate(**data)
        assert "must be in the future." in str(exc_info.value)


@pytest.mark.parametrize(
    "start_time,timedelta_,is_valid",
    (
        (datetime.now() + timedelta(minutes=5), timedelta(minutes=35), True),
        (datetime.now() + timedelta(hours=1), timedelta(hours=1, minutes=35), True),
        (datetime.now() + timedelta(minutes=5), timedelta(), False),
    ),
)
def test_reservation_create_end_time_validators(
    start_time: datetime, timedelta_: timedelta, is_valid: bool
):
    end_time = start_time + timedelta_
    data = {
        "facility_id": str(uuid.uuid4()),
        "payment_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "start_time": start_time,
        "end_time": end_time,
        "price": fake.pydecimal(left_digits=2, right_digits=2, positive=True),
    }

    if is_valid:
        try:
            reservation = ReservationCreate(**data)
            assert reservation.start_time.tzinfo == pytz.timezone("UTC")
        except ValueError:
            pytest.fail(f"End time {end_time!r} should be valid")
    else:
        with pytest.raises(ValueError) as exc_info:
            ReservationCreate(**data)
        assert "must be after start time." in str(exc_info.value)
