import uuid
from datetime import datetime, timedelta

import pytest
import pytz
from faker import Faker

from reshal_api.reservation.schemas import ReservationCreate, ReservationCreateBase

fake = Faker()


@pytest.mark.parametrize(
    "start_time,is_valid",
    (
        (datetime.now() + timedelta(minutes=1), True),
        (datetime.now(tz=pytz.timezone("Europe/Warsaw")) + timedelta(hours=1), True),
        (datetime.now(), False),
        (datetime.now() + timedelta(minutes=-1), False),
    ),
)
def test_reservation_create_base_start_time_validators(
    start_time: datetime, is_valid: bool
):
    data = {"facility_id": str(uuid.uuid4()), "start_time": start_time}

    if is_valid:
        try:
            reservation = ReservationCreateBase(**data)
            assert reservation.start_time.tzinfo == pytz.timezone("UTC")
        except ValueError:
            pytest.fail(f"Start time {start_time!r} should be valid")
    else:
        with pytest.raises(ValueError) as exc_info:
            ReservationCreateBase(**data)
        assert "Start time must be in the future." in str(exc_info.value)


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
        assert "Start time must be in the future." in str(exc_info.value)


@pytest.mark.parametrize(
    "start_time,timedelta_,is_valid",
    (
        (datetime.now() + timedelta(minutes=5), timedelta(minutes=10), True),
        (
            datetime.now(tz=pytz.timezone("Europe/Warsaw")) + timedelta(hours=1),
            timedelta(minutes=10),
            True,
        ),
        (datetime.now() + timedelta(minutes=5), timedelta(minutes=-10), False),
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
        assert "End time must be after start time." in str(exc_info.value)
